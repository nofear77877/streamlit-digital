import streamlit as st
import pandas as pd
import os
import warnings
import matplotlib.pyplot as plt  # 导入绘图库
import seaborn as sns  # 导入seaborn美化图表
warnings.filterwarnings('ignore')

# 全局设置matplotlib中文字体（基础配置）
plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题
sns.set_style("whitegrid")

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
        /* 标题样式 */
        h1 {
            color: #2E86AB; 
            padding-bottom: 0.5rem; 
            border-bottom: 2px solid #2E86AB;
            margin-bottom: 1.5rem;
        }
        /* 指标卡片样式 */
        .stMetric {
            background: white; 
            padding: 1rem; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.05); 
            margin-bottom: 1rem;
        }
        /* 按钮样式（占满容器宽度） */
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
        /* 表格样式（自适应宽度） */
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
        /* 分隔线样式 */
        .divider {
            height: 2px;
            background-color: #e0e0e0;
            margin: 1rem 0;
            border: none;
        }
    </style>
    """, unsafe_allow_html=True)

# ===================== 数据加载函数 =====================
@st.cache(ttl=3600, show_spinner="正在加载数据...", suppress_st_warning=True)
def load_data():
    try:
        # 文件路径（相对路径，与代码文件同目录）
        file_path = '1999-2023年数字化转型指数汇总.csv' 
        
        if not os.path.exists(file_path):
            return {
                "status": "error", 
                "msg": f"文件不存在：{file_path}\n请检查路径是否正确"
            }
        
        # 自动识别文件格式+编码
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
                return {"status": "error", "msg": "无法识别CSV编码，请用Excel另存为UTF-8格式"}
        elif file_ext in ['.xlsx', '.xlsm']:
            try:
                df = pd.read_excel(file_path, sheet_name='Sheet1', engine='openpyxl')
            except ImportError:
                return {"status": "error", "msg": "读取Excel需安装：pip install openpyxl==3.0.10"}
            except Exception as e:
                return {"status": "error", "msg": f"Excel读取失败：{str(e)}"}
        else:
            return {"status": "error", "msg": f"不支持的格式：{file_ext}，仅支持CSV/Excel"}
        
        # 检查必要列
        required_cols = ['股票代码', '企业名称', '年份', '数字化转型指数']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return {"status": "error", "msg": f"缺少列：{', '.join(missing_cols)}"}
        
        # 数据清洗
        df['股票代码'] = df['股票代码'].astype(str).str.zfill(6)
        df['企业名称'] = df['企业名称'].astype(str).str.strip()
        df['年份'] = df['年份'].astype(int)
        df['数字化转型指数'] = df['数字化转型指数'].round(2)
        df = df[(df['年份'] >= 1999) & (df['年份'] <= 2023)]
        
        return {
            "status": "success", 
            "data": df,
            "msg": f"加载成功！{len(df):,} 条记录 | {df['股票代码'].nunique()} 家公司"
        }
    
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
        
        if selected_year != "全部年份":
            result_df = result_df[result_df['年份'] == int(selected_year)]
        
        return result_df.sort_values('年份', ascending=False)
    except Exception as e:
        st.error(f"搜索出错：{str(e)}")
        return pd.DataFrame()

# ===================== 绘制趋势图函数（已修复中文显示） =====================
def plot_trend_chart(result_df):
    # 强制设置当前图表的中文字体（双重保障）
    plt.rcParams["font.family"] = ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
    
    # 如果查询结果包含多家公司，按公司分组绘图
    companies = result_df['企业名称'].unique()
    plt.figure(figsize=(12, 6))
    
    for company in companies:
        company_data = result_df[result_df['企业名称'] == company].sort_values('年份')
        sns.lineplot(
            x='年份', 
            y='数字化转型指数', 
            data=company_data,
            marker='o',  # 数据点标记
            label=company,
            linewidth=2
        )
    
    # 标题和标签明确指定中文字体
    plt.title('数字化转型指数趋势（1999-2023）', fontsize=15, fontproperties="SimHei")
    plt.xlabel('年份', fontsize=12, fontproperties="SimHei")
    plt.ylabel('数字化转型指数', fontsize=12, fontproperties="SimHei")
    plt.xticks(rotation=45)
    
    # 图例设置中文字体
    plt.legend(
        title='企业名称', 
        bbox_to_anchor=(1.05, 1), 
        loc='upper left',
        prop={"family": ["SimHei", "WenQuanYi Micro Hei", "Heiti TC"]},  # 图例文字字体
        title_fontproperties="SimHei"  # 图例标题字体
    )
    
    plt.tight_layout()  # 自动调整布局，避免文字被截断
    return plt

# ===================== 结果展示函数 =====================
def display_results(result_df, search_input, selected_year):
    if result_df.empty:
        st.warning("未找到匹配数据！示例：600008（首创股份）")
        return
    
    # 基础统计
    total = len(result_df)
    companies = result_df['股票代码'].nunique()
    year_range = f"{result_df['年份'].min()}-{result_df['年份'].max()}" if selected_year == "全部年份" else selected_year
    st.success(f"搜索结果 | {total:,} 条 | {companies} 家公司 | 年份：{year_range}")
    
    # 关键指标
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("平均指数", f"{result_df['数字化转型指数'].mean():.2f}")
    with col2:
        st.metric("最高指数", f"{result_df['数字化转型指数'].max():.2f}")
    with col3:
        st.metric("最低指数", f"{result_df['数字化转型指数'].min():.2f}")
    
    # 显示趋势折线图（仅当查询全部年份时）
    if selected_year == "全部年份":
        st.subheader("📈 数字化转型指数趋势图")
        fig = plot_trend_chart(result_df)
        st.pyplot(fig)
        plt.close()  # 关闭图表释放资源
    
    # 详细表格
    st.subheader("详细数据")
    display_df = result_df.copy().reset_index(drop=True)
    display_df.index = display_df.index + 1
    st.dataframe(display_df[['股票代码', '企业名称', '年份', '数字化转型指数']])
    
    # CSV下载
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
    
    # 页面标题
    st.title("📊 上市公司数字化转型指数查询系统")
    st.markdown("### 📅 1999-2023年 | 📌 股票代码/企业名称查询")
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    
    # 加载数据
    data_result = load_data()
    if data_result["status"] == "error":
        st.error(data_result["msg"])
        return
    else:
        st.info(data_result["msg"])
        df = data_result["data"]
    
    # 侧边栏
    with st.sidebar:
        st.header("🔍 查询设置")
        st.markdown('<hr class="divider" style="margin:0.5rem 0;">', unsafe_allow_html=True)
        
        # 搜索类型
        st.session_state.search_type = st.radio(
            "查询方式",
            ["股票代码", "企业名称"],
            index=0 if st.session_state.search_type == "股票代码" else 1
        )
        
        # 输入框
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
        
        # 年份选择
        year_options = ["全部年份"] + sorted(df['年份'].unique())
        try:
            year_index = year_options.index(st.session_state.selected_year)
        except ValueError:
            year_index = 0
        st.session_state.selected_year = st.selectbox("查询年份", year_options, index=year_index)
        
        st.markdown('<hr class="divider" style="margin:0.5rem 0;">', unsafe_allow_html=True)
        
        # 按钮
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            execute_search = st.button("执行查询")
        with col_btn2:
            if st.button("重置"):
                st.session_state.search_input = ""
                st.session_state.selected_year = "全部年份"
                st.session_state.search_results = None
                st.info("已重置！")
    
    # 执行查询
    if execute_search:
        if not st.session_state.search_input.strip():
            st.warning("请输入查询内容！")
        else:
            search_result_df = search_data(
                df,
                st.session_state.search_input,
                st.session_state.search_type,
                st.session_state.selected_year
            )
            st.session_state.search_results = search_result_df
            display_results(search_result_df, st.session_state.search_input, st.session_state.selected_year)
    
    # 历史结果
    elif st.session_state.search_results is not None:
        display_results(
            st.session_state.search_results,
            st.session_state.search_input,
            st.session_state.selected_year
        )
    
    # 示例数据
    else:
        st.subheader("💡 数据示例（前10条）")
        sample_df = df.head(10).copy()
        sample_df.index = sample_df.index + 1
        st.dataframe(sample_df[['股票代码', '企业名称', '年份', '数字化转型指数']])
        st.info("请在左侧边栏输入查询条件，点击「执行查询」！")

if __name__ == "__main__":
    main()
