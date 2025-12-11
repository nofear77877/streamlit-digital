import streamlit as st
import pandas as pd
import os
import warnings
import plotly.express as px
warnings.filterwarnings('ignore')

# ===================== 页面基础配置 =====================
st.set_page_config(
    page_title="上市公司数字化转型指数查询系统",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== Session State 初始化 =====================
if 'selected_year' not in st.session_state:
    st.session_state.selected_year = "全部年份"
if 'search_input' not in st.session_state:
    st.session_state.search_input = ""
if 'search_type' not in st.session_state:
    st.session_state.search_type = "股票代码"
if 'search_results' not in st.session_state:
    st.session_state.search_results = None

# ===================== 自定义CSS样式 =====================
def load_basic_css():
    st.markdown("""
    <style>
        h1 {
            color: #2E86AB; 
            padding-bottom: 0.5rem; 
            border-bottom: 2px solid #2E86AB;
            margin-bottom: 1.5rem;
        }
        .stMetric {
            background: white; 
            padding: 1rem; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
            margin-bottom: 1rem;
        }
        .stButton > button {
            background: #2E86AB; 
            color: white; 
            border: none; 
            border-radius: 6px;
            padding: 0.4rem 1rem;
            width: 100%;
            margin: 0.2rem 0;
        }
        .stButton > button:hover {
            background: #1E6B8B;
        }
        .dataframe {
            width: 100% !important;
            border-radius: 8px; 
            overflow: hidden; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .dataframe thead th {
            background: #2E86AB; 
            color: white; 
            text-align: center;
        }
        .divider {
            height: 2px;
            background-color: #e0e0e0;
            margin: 1rem 0;
            border: none;
        }
    </style>
    """, unsafe_allow_html=True)

# ===================== 数据加载函数 =====================
@st.cache_data(ttl=3600, show_spinner="正在加载数据...")
def load_data():
    try:
        file_path = '1999-2023年数字化转型指数汇总.csv' 
        if not os.path.exists(file_path):
            return {"status": "error", "msg": f"文件不存在：{file_path}"}
        
        file_ext = os.path.splitext(file_path)[1].lower()
        df = None
        if file_ext == '.csv':
            encodings = ['gbk', 'gb2312', 'utf-8-sig', 'latin-1']
            for enc in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=enc)
                    break
                except:
                    continue
            if df is None:
                return {"status": "error", "msg": "无法识别CSV编码"}
        elif file_ext in ['.xlsx', '.xlsm']:
            try:
                df = pd.read_excel(file_path, sheet_name='Sheet1', engine='openpyxl')
            except Exception as e:
                return {"status": "error", "msg": f"Excel读取失败：{str(e)}"}
        else:
            return {"status": "error", "msg": "不支持的格式"}
        
        required_cols = ['股票代码', '企业名称', '年份', '数字化转型指数']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return {"status": "error", "msg": f"缺少列：{', '.join(missing_cols)}"}
        
        df['股票代码'] = df['股票代码'].astype(str).str.zfill(6)
        df['企业名称'] = df['企业名称'].str.strip()
        df['年份'] = df['年份'].astype(int)
        df['数字化转型指数'] = df['数字化转型指数'].round(2)
        df = df[(df['年份'] >= 1999) & (df['年份'] <= 2023)]
        
        return {"status": "success", "data": df, "msg": f"加载成功！{len(df):,} 条记录"}
    except Exception as e:
        return {"status": "error", "msg": f"加载失败：{str(e)}"}

# ===================== 搜索功能函数 =====================
def search_data(df, search_input, search_type, selected_year):
    try:
        result_df = df.copy()
        if search_type == "股票代码":
            search_code = str(search_input).strip().zfill(6)
            result_df = result_df[result_df['股票代码'].str.contains(search_code, na=False)]
        else:
            search_name = str(search_input).strip().lower()
            result_df = result_df[result_df['企业名称'].str.lower().str.contains(search_name, na=False)]
        
        # 即使选单一年份，也保留所有年份数据（用于画趋势图）
        year_filtered_df = result_df.copy()
        if selected_year != "全部年份":
            year_filtered_df = year_filtered_df[year_filtered_df['年份'] == int(selected_year)]
        
        return result_df, year_filtered_df
    except Exception as e:
        st.error(f"搜索出错：{str(e)}")
        return pd.DataFrame(), pd.DataFrame()

# ===================== 绘制趋势图函数（修复标题拼接错误） =====================
def plot_trend_chart(full_result_df, selected_year):
    # 关键修复：将selected_year转为字符串再拼接
    title_suffix = f"|{str(selected_year)}年" if selected_year != "全部年份" else ""
    fig = px.line(
        full_result_df,
        x='年份',
        y='数字化转型指数',
        color='企业名称',
        markers=True,
        title=f'数字化转型指数趋势（1999-2023）{title_suffix}',  # 修复拼接错误
        labels={
            '年份': '年份',
            '数字化转型指数': '数字化转型指数',
            '企业名称': '企业名称'
        }
    )
    
    # 高亮选中的年份（如果是单年份）
    if selected_year != "全部年份":
        target_year = int(selected_year)
        for trace in fig.data:
            year_idx = full_result_df[(full_result_df['企业名称'] == trace.name) & (full_result_df['年份'] == target_year)].index
            if len(year_idx) > 0:
                idx = year_idx[0]
                fig.add_annotation(
                    x=target_year,
                    y=full_result_df.loc[idx, '数字化转型指数'],
                    text=f'{target_year}年: {full_result_df.loc[idx, "数字化转型指数"]}',
                    showarrow=True,
                    arrowhead=2,
                    ax=0,
                    ay=-30
                )
    
    fig.update_layout(
        width=800,
        height=500,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# ===================== 结果展示函数 =====================
def display_results(full_result_df, year_filtered_df, search_input, selected_year):
    if year_filtered_df.empty:
        st.warning("未找到匹配数据！示例：600008（首创股份）")
        return
    
    total = len(year_filtered_df)
    companies = year_filtered_df['股票代码'].nunique()
    year_text = selected_year if selected_year != "全部年份" else f"{full_result_df['年份'].min()}-{full_result_df['年份'].max()}"
    st.success(f"搜索结果 | {total:,} 条 | {companies} 家公司 | 年份：{year_text}")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("平均指数", f"{year_filtered_df['数字化转型指数'].mean():.2f}")
    with col2:
        st.metric("最高指数", f"{year_filtered_df['数字化转型指数'].max():.2f}")
    with col3:
        st.metric("最低指数", f"{year_filtered_df['数字化转型指数'].min():.2f}")
    
    st.subheader("📈 数字化转型指数趋势图")
    fig = plot_trend_chart(full_result_df, selected_year)
    st.plotly_chart(fig)
    
    st.subheader("详细数据")
    display_df = year_filtered_df.copy().reset_index(drop=True)
    display_df.index = display_df.index + 1
    st.dataframe(display_df[['股票代码', '企业名称', '年份', '数字化转型指数']])
    
    csv_data = display_df[['股票代码', '企业名称', '年份', '数字化转型指数']].to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="下载CSV数据",
        data=csv_data,
        file_name=f"转型指数_查询结果_{search_input}_{selected_year}.csv",
        mime="text/csv"
    )

# ===================== 主程序 =====================
def main():
    load_basic_css()
    
    st.title("📊 上市公司数字化转型指数查询系统")
    st.markdown("### 📅 1999-2023年 | 📌 股票代码/企业名称查询")
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    
    data_result = load_data()
    if data_result["status"] == "error":
        st.error(data_result["msg"])
        return
    else:
        st.info(data_result["msg"])
        df = data_result["data"]
    
    with st.sidebar:
        st.header("🔍 查询设置")
        st.markdown('<hr class="divider" style="margin:0.5rem 0;">', unsafe_allow_html=True)
        
        st.session_state.search_type = st.radio(
            "查询方式",
            ["股票代码", "企业名称"],
            index=0 if st.session_state.search_type == "股票代码" else 1
        )
        
        if st.session_state.search_type == "股票代码":
            st.session_state.search_input = st.text_input(
                "股票代码",
                value=st.session_state.search_input,
                placeholder="600008",
                max_chars=6
            )
        else:
            st.session_state.search_input = st.text_input(
                "企业名称",
                value=st.session_state.search_input,
                placeholder="首创"
            )
        
        st.markdown('<hr class="divider" style="margin:0.5rem 0;">', unsafe_allow_html=True)
        
        year_options = ["全部年份"] + sorted(df['年份'].unique().astype(str))  # 年份转为字符串
        try:
            year_index = year_options.index(str(st.session_state.selected_year))
        except ValueError:
            year_index = 0
        st.session_state.selected_year = st.selectbox("查询年份", year_options, index=year_index)
        
        st.markdown('<hr class="divider" style="margin:0.5rem 0;">', unsafe_allow_html=True)
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            execute_search = st.button("执行查询")
        with col_btn2:
            if st.button("重置"):
                st.session_state.search_input = ""
                st.session_state.selected_year = "全部年份"
                st.session_state.search_results = None
                st.info("已重置！")
    
    if execute_search:
        if not st.session_state.search_input.strip():
            st.warning("请输入查询内容！")
        else:
            full_result_df, year_filtered_df = search_data(
                df,
                st.session_state.search_input,
                st.session_state.search_type,
                st.session_state.selected_year
            )
            st.session_state.full_result = full_result_df
            st.session_state.year_filtered = year_filtered_df
            display_results(full_result_df, year_filtered_df, st.session_state.search_input, st.session_state.selected_year)
    
    elif st.session_state.get('full_result') is not None:
        display_results(
            st.session_state.full_result,
            st.session_state.year_filtered,
            st.session_state.search_input,
            st.session_state.selected_year
        )
    
    else:
        st.subheader("💡 数据示例（前10条）")
        sample_df = df.head(10).copy()
        sample_df.index = sample_df.index + 1
        st.dataframe(sample_df[['股票代码', '企业名称', '年份', '数字化转型指数']])
        st.info("请在左侧边栏输入查询条件，点击「执行查询」！")

if __name__ == "__main__":
    main()
