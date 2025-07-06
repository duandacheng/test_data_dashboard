import streamlit as st
import pandas as pd
import plotly.express as px
from calculate_defect import calculate_defect
from datetime import datetime, date, timedelta

current_year = datetime.now().year

st.set_page_config(
    page_title="测试数据分析看板",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {background-color: #4CAF50; color: white;}
    .stTextInput>div>div>input {background-color: #e8f5e9;}
    .stFileUploader>div>div>div>button {background-color: #2196F3; color: white;}
    .reportview-container .main .block-container {padding-top: 2rem;}
    .sidebar .sidebar-content {background-color: #e3f2fd;}
    .metric-card {background: white; border-radius: 10px; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    .header {color: #1e88e5; padding-bottom: 10px; border-bottom: 2px solid #bbdefb;}
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("📁 数据源设置")
st.sidebar.markdown('---')

option = st.sidebar.radio("请选择数据源", (['上传文件', '指定文件路径']))
df = None

if option == '上传文件':
    uploaded_files = st.sidebar.file_uploader("上传数据文件（Excel）", type=['xlsx', 'xls'], accept_multiple_files=True)

    # 初始化变量
    df1 = df2 = df3 = df4 = None
    # 初始化session state存储文件
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {}

    if uploaded_files:
        # 存储文件数据到session_state
        for file in uploaded_files:
            st.session_state.uploaded_files[file.name] = {  # file.name为key，{data: size: }为value
                "data": pd.read_excel(file),
                "size": file.size
            }
            st.sidebar.success(f"已添加: {file.name}")

        for filename, file_data in st.session_state.uploaded_files.items():
            try:
                if "测试查询" in filename:
                    df1 = file_data["data"]
                elif "缺陷" in filename:
                    df2 = file_data.get("data")
                elif "节省" in filename:
                    df3 = file_data.get("data")
                elif "工具" in filename:
                    df4 = file_data.get("data")
            except (KeyError, AttributeError) as e:  # 明确异常类型
                st.sidebar.error(f"文件结构错误: {str(e)}")
                break

    this_year_data = {}

    # ------Part1:测试工单数据部分---------
    if df1 is not None:
        # 处理df
        df1.columns = df1.iloc[0, :]  # 重置列索引
        df1 = df1.drop(0)  # 删除索引为0的行


        def initial_masks(data):
            # 删除无效工单
            mask = (
                       data['工单环节'].isin(['取消', '新建'])
                   ) & (
                       data['当前处理人'].isna()  # 空值
                   )
            data_filtered = data[~mask]

            # 过滤出未完结工单
            mask1 = (
                        data_filtered['工单环节'].isin(['产品负责人确认实际工作量'])
                    ) & (
                        data_filtered['工单状态'].isin(['测试完成中'])

                    )
            return mask, mask1, data_filtered


        mask, mask1, data_filtered = initial_masks(df1)

        first_day = date(datetime.now().year, 1, 1)   # 获取当年第一天
        last_day = date(datetime.now().year + 1, 1, 1) - timedelta(days=1)  # 获取当年最后一天（通过次年第一天减1天）

        # 准备今年数据
        def this_year_data(data_filtered):
            s = data_filtered['工单编号']
            date_str = s.str.extract(r"(\d{8})")  # 提取每个元素的8位数字
            print(date_str.dtypes)  # 提取的时间结果
            # 将series先转换为string，再转换为时间格式DateTmie64（pandas的Timestamp类型）,最后转换为date
            date_str = pd.to_datetime(date_str.iloc[:, 0].astype(str), format="%Y%m%d",
                                      errors="coerce").dt.date
            # mask3 = date_str >= pd.to_datetime('20250101', format='%Y%m%d')  # 今年布尔矩阵
            mask3 = (date_str >= first_day) & (date_str <= last_day)
            count3 = mask3.sum()  # 2025年新增受理工单数

            # 全年工单状态
            this_year_data = data_filtered[mask3]

            return count3, this_year_data


        count3, this_year_data = this_year_data(data_filtered)

        df_ = this_year_data  # 今年数据

        st.title("📊 验收测试数据分析看板")

        # st.markdown(f"<div class='header'><h3>数据集概览: {df_.shape[0]} 行 × {df_.shape[1]} 列</h3></div>",
        #             unsafe_allow_html=True)
        st.markdown(f"<div class='header'><h3>测试工单数据集概览</h3></div>",
                    unsafe_allow_html=True)
        # st.header("📈测试工单数据看板")
        # st.markdown("---")

        # 关键指标卡片
        st.subheader("关键指标")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("测试工单数", f"{count3}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("发现缺陷数",
                      f"{df_['问题总数'].fillna(0).astype(int).sum()}" if '问题总数' in df_.columns else "N/A")
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("执行用例数",
                      f"{df_['用例总数'].fillna(0).astype(int).sum()}" if '用例总数' in df_.columns else "N/A")
            st.markdown("</div>", unsafe_allow_html=True)

        cost = round(pd.to_numeric(df_['订单实际总价不含税（元）']).sum(), 2)

        with col4:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("已执行测试费用",
                      f"{cost}" if '订单实际总价不含税（元）' in df1.columns else "N/A")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")

        # 时间序列分析
        st.subheader("测试受理数据")
        if '创建时间' in df_.columns:
            # 确保日期列是日期类型
            try:
                df_['创建时间'] = pd.to_datetime(df_['创建时间'])
            except:
                st.warning("日期列转换失败，请确保日期格式正确")

            # 时间序列图表
            time_col, state_col = st.columns(2)

            with time_col:
                time_group = st.radio("时间粒度",
                                      ['日', '周', '月'],
                                      index=0,
                                      horizontal=True,
                                      label_visibility="collapsed")

                if time_group == '日':
                    freq_counts = df_['创建时间'].dt.date.value_counts().sort_index()
                    freq_title = '每日受理工单数'

                elif time_group == '周':
                    # 1. 按ISO周重采样（周一作为周开始）
                    weekly_counts = df_.resample('W-MON', on='创建时间').size()

                    # 2. 创建格式化的周标签（ISO格式更准确）
                    weekly_labels = [
                        f"{isoyear}-{isoweek:02d}"
                        for isoyear, isoweek in zip(
                            weekly_counts.index.isocalendar().year,
                            weekly_counts.index.isocalendar().week
                        )
                    ]
                    fig_weekly = px.bar(
                        x=weekly_labels,
                        y=weekly_counts.values,
                        labels={'x': '周(年-周数)', 'y': '工单数'},
                        title='每周受理工单数',
                        text=weekly_counts.values,  # 在柱子上显示数值
                        color_discrete_sequence=['#ff7f0e']
                    )

                    fig_weekly.update_layout(
                        xaxis_type='category',
                        xaxis=dict(
                            categoryorder='array',
                            categoryarray=weekly_labels,
                            tickangle=45  # 倾斜标签避免重叠
                        )
                    )
                    # 添加数值标签
                    fig_weekly.update_traces(textposition='outside')

                    st.plotly_chart(fig_weekly)

                elif time_group == '月':
                    freq_labels = df_["创建时间"].dt.strftime('%Y-%m')
                    freq_counts = freq_labels.value_counts().sort_index()  # 返回series对象，索引为月份，值为频次
                    freq_title = '每月受理工单数'

                    # 创建柱状图
                if time_group in ['月', '日']:
                    fig = px.bar(
                        freq_counts,
                        x=freq_counts.index,
                        y=freq_counts.values,
                        title=freq_title,
                        labels={'数量': '工单数'},
                        color_discrete_sequence=['#ff7f0e']  # 设置柱状图颜色
                    )
                    # 更新布局
                    fig.update_layout(
                        xaxis_title=None,
                        yaxis_title="工单数",
                        hovermode="x unified",
                        plot_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(
                            tickformat='%Y-%m-%d' if time_group in ["日", "周"] else '%Y-%m',
                            gridcolor='lightgray'
                        ),
                        yaxis=dict(
                            gridcolor='lightgray'
                        )
                    )

                    st.plotly_chart(fig, use_container_width=True)

            # 工单状态统计
            state_counts = df1['工单状态'].value_counts().reset_index()
            state_counts.columns = ['工单状态', '数量']
            with state_col:
                fig_state = px.pie(
                    state_counts,
                    names='工单状态',
                    values='数量',
                    title='工单状态',
                    hover_data=['数量'],

                )
                st.plotly_chart(fig_state, use_container_width=True)

            industry_col, target_col = st.columns(2)

            with target_col:
                counts_target = df_['提测用途'].value_counts().reset_index()  # 统计数据值出现频次并转换为dataframe类型
                counts_target.columns = ['用途', '频次']

                counts_target['占比(%)'] = (counts_target['频次'] / counts_target['频次'].sum() * 100).round(1)

                fig_target = px.bar(
                    counts_target,
                    x='频次',
                    y='用途',
                    orientation='h',
                    text='占比(%)',
                    color='频次',
                    color_continuous_scale='Blues',
                    title='提测用途与占比分布'
                )

                # 优化图表样式
                fig_target.update_traces(texttemplate='%{text}%', textposition='outside')
                fig_target.update_layout(
                    yaxis={'categoryorder': 'total ascending'},
                    xaxis_title="频次",
                    yaxis_title="提测用途",
                    height=500
                )
                st.plotly_chart(fig_target, use_container_width=True)

            with industry_col:
                counts_industry = df_['所属行业'].value_counts().reset_index()
                counts_industry.columns = ['行业', '频次']

                fig_industry = px.pie(
                    counts_industry,
                    values='频次',
                    names='行业',
                    title='提测项目所属行业',
                    hover_data=['频次'],
                    labels={'频次': '提测次数'}
                )
                st.plotly_chart(fig_industry, use_container_width=True)

        else:
            st.warning("数据集中没有找到日期列，无法进行时间序列分析")

        st.markdown("---")

        # 按部门统计缺陷饼图数据
        list_dept = ["教育产品中心", "研发一部", "低空经济技术研发运营中心", "研发二部", "医疗产品中心", "农商文旅产品中心"]
        dept_defect = []
        for i in list_dept:
            mask_dept = df_["提测部门"].isin([i])
            df_dept = df_[mask_dept]  # 按部门切片
            df_dept_sum = df_dept["问题总数"].fillna(0).astype(int).sum()
            dept_defect.append(df_dept_sum)

        data = {'部门': list_dept,
                '缺陷数': dept_defect}
        data = pd.DataFrame(data)

        high_level_defect, total_defect, pf_defect, ep_defect = calculate_defect(df_['问题明细'], 0)

        st.subheader("测试缺陷分析")
        st.markdown(
            f"""
                {current_year}年发现缺陷共计{total_defect}个，
                中高等级功能缺陷<span style='color:red; font-size:2.2em'>{high_level_defect}</span>个，
                性能缺陷<span style='color:red; font-size:2.2em'>{pf_defect}</span>个，
                体验缺陷<span style='color:red; font-size:2.2em'>{ep_defect}</span>个
            """,
            unsafe_allow_html=True
        )
        defect_col1, defect_col2 = st.columns(2)
        with defect_col1:
            fig_dept_defect = px.pie(data,
                                     values='缺陷数',
                                     names='部门',
                                     title='各部门缺陷数占比',
                                     hover_data=['缺陷数'],
                                     labels={'缺陷数': '缺陷数量'}
                                     )
            st.plotly_chart(fig_dept_defect)

        with defect_col2:
            # 按问题总数降序排序并取前10
            df_['显示名称'] = df_['项目名称'].str.slice(0, 20) + '_' + df_['提测版本'].astype(str)
            df_['问题总数'] = df_['问题总数'].fillna(0).astype(int)  # 转换为整形数值，否则排序是按字符而非数值
            top10 = df_.sort_values('问题总数', ascending=False).head(10)
            fig_top10_defect_pro = px.bar(top10,
                                          x='显示名称' if '显示名称' in top10.columns else '项目名称',
                                          y='问题总数',
                                          title='缺陷数TOP10项目',
                                          labels={'x': '项目', 'y': '缺陷数'}
                                          )
            st.plotly_chart(fig_top10_defect_pro)

        st.markdown('---')

        st.subheader('测试用例分析')
        df_case = this_year_data
        case_total = df_case['用例总数'].fillna(0).astype(int).sum()
        pass_case_total = df_case['通过用例数'].fillna(0).astype(int).sum()
        case_pass_ratio = round(pass_case_total / case_total * 100, 2)
        st.markdown(
            f"""
                {current_year}年执行测试用例共计{case_total}个，
                通过用例数<span style='color:red; font-size:2.2em'>{pass_case_total}</span>个，
                用例通过率<span style='color:red; font-size:2.2em'>{case_pass_ratio}%</span>
            """,
            unsafe_allow_html=True
        )

        case_col, period_col = st.columns(2)
        # 测试项目用例及工作量
        with case_col:
            case_workload = df_case.loc[
                df_case['用例总数'].notna(), ['实际总人天', '用例总数', '所属行业', '项目名称']]  # loc[行条件, 列列表]

            fig_case = px.scatter(
                case_workload,
                x='实际总人天',
                y='用例总数',
                color='所属行业',
                size=case_workload['用例总数'].astype(int),
                hover_data='项目名称',
                title='测试项目用例及工作量',
                labels={
                    '实际总人天': '测试工作量（人天）'
                }
            )

            st.plotly_chart(fig_case, use_container_width=True)

        period_series = df_case['测试实际时长（工作日）'].dropna().astype(int)
        mean_value = period_series.mean()
        # 测试时长（工作日）
        with period_col:
            fig_period = px.scatter(
                period_series,
                x=range(1, len(period_series) + 1),
                y='测试实际时长（工作日）',
                title='测试时长（工作日）',
                labels={
                    'x': '项目序号'
                }
            )

            # 动态调整现状太小和颜色
            fig_period.update_traces(
                marker=dict(
                    size=12,  # 统一大小
                    symbol='triangle-up',  # 强制所有点改为三角形
                    color='red'  # 边框样式
                )
            )

            # 添加平均值横线
            fig_period.add_hline(
                y=mean_value,
                line_dash="dash",  # 虚线样式
                line_color="green",
                annotation_text=f"平均值: {mean_value:.1f}",  # 显示数值
                annotation_position="top left"
            )
            st.plotly_chart(fig_period, use_container_width=True)

    # -------------第二部分：缺陷库看板----------------
    # 排序柱状图
    def plot_sorted_counts(series, title):
        # 统计频次并排序
        counts = series.value_counts().sort_values(ascending=False)
        # 计算百分比
        percent = round(counts / counts.sum() * 100, 1)
        # 合并数据
        df_sort = pd.DataFrame({'类别': counts.index,
                                '缺陷数': counts.values,
                                '百分比': percent.astype(str) + '%'})

        # 绘制柱状图
        fig_sort = px.bar(df_sort,
                          x='类别',
                          y='缺陷数',
                          text='百分比',
                          title=title)
        st.plotly_chart(fig_sort, use_container_width=True)

    def plot_sort_counts_pie(series, values, names, title, color_diy, label_name):
        fig_pie = px.pie(
            series,
            values=values,
            names=names,
            title=title,
            hole=0.5,
            color=names,  # 显式指定着色列
            color_discrete_map=color_diy,
            # hover_data=[''],
            labels={'count': label_name}
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    if df2 is not None:
        # st.markdown('---')
        # st.markdown("<hr>", unsafe_allow_html=True)

        st.markdown("""
        <div style="
            height: 4px;
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
            margin: 25px 0;
            border-radius: 2px;
        "></div>
        """, unsafe_allow_html=True)

        df2.columns = df2.iloc[0, :]
        df2 = df2.drop(0)
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)
        st.header("📈缺陷库运营数据分析看板")
        # st.dataframe(df2)

        # 当年归档的缺陷数据
        df2_current_year = df2[df2['工单编号'].str.contains(f'-{current_year}')]

        project_unique_counts = df2_current_year['产品名称'].nunique()  # 统计去重项目数
        current_year_defects = len(df2_current_year)  # 当年归档缺陷数
        finish_analysis_counts = df2_current_year['备注说明'].count()
        finish_analysis_ratio = round((finish_analysis_counts / current_year_defects) * 100, 1)

        st.markdown(
            f"""
                {current_year}年缺陷库归档项目<span style='color:red; font-size:2.2em'>{project_unique_counts}</span>个，
                归档缺陷<span style='color:red; font-size:2.2em'>{current_year_defects}</span>个，
                完成缺陷根因分析<span style='color:red; font-size:2.2em'>{finish_analysis_counts}</span>个，
                根因分析完成率<span style='color:red; font-size:2.2em'>{finish_analysis_ratio}%</span>
            """,
            unsafe_allow_html=True
        )

        st.dataframe(df2_current_year.reset_index().iloc[:, 2:])

        defect_type, defect_why = st.columns(2)
        with defect_type:
            # 使用正则表达式去除括号及括号内内容
            df2_defect_type = df2_current_year['缺陷类型'].str.replace(r'\（[^）]*\）', '', regex=True)
            plot_sorted_counts(df2_defect_type.dropna(), '缺陷类型分析')

        with defect_why:
            plot_sorted_counts(df2_current_year['缺陷引入阶段'].dropna(), '缺陷引入阶段分析')

        closed_defects_ratio, common_defects_ratio = st.columns(2)

        with closed_defects_ratio:
            df2_defect_states = df2_current_year['问题状态'].value_counts().reset_index()  # 默认剔除nan数值
            color_states = {'打开': 'green', '技支复测关闭': 'silver', '评审关闭': 'gray', '挂起': 'brown'}
            # st.dataframe(df2_defect_states)
            plot_sort_counts_pie(df2_defect_states, 'count', '问题状态', f'{current_year}年入库闭环率', color_diy=color_states, label_name='缺陷数')

        with common_defects_ratio:
            df2_defect_common = df2_current_year['是否共性缺陷'].value_counts().reset_index()
            color_common = {'是': 'gold', '否': '#0068C9'}
            plot_sort_counts_pie(df2_defect_common, 'count', '是否共性缺陷', '共性缺陷占比', color_diy=color_common, label_name='数量')

#  ------第三部分：节省费用统计---------
    if len(this_year_data) > 0 and df3 is not None:
        df_money = this_year_data
        this_year_finish_data = df_money[df_money['结束日期'].notna()]
        this_year_finish_data['结束日期'] = pd.to_datetime(this_year_finish_data['结束日期'])

        # 新增一列节省费用
        this_year_finish_data['节省费用'] = this_year_finish_data['已下订单总价不含税（元）'].astype(float) - this_year_finish_data['订单实际总价不含税（元）'].astype(float)
        this_year_finish_data_0 = this_year_finish_data[this_year_finish_data['是否复测'] == '否']  # 已完成的非复测工单
        this_year_finish_data_1 = this_year_finish_data[this_year_finish_data['是否复测'] == '是']  # 已完成的复测工单
        # st.dataframe(this_year_finish_data)

        save_0 = this_year_finish_data_0.groupby(this_year_finish_data_0['结束日期'].dt.strftime('%Y-%m'))['节省费用'].sum()
        save_0.name = '口径1-实际较预估节省'
        # st.dataframe(save_0)
        save_1 = this_year_finish_data_1.groupby(this_year_finish_data_1['结束日期'].dt.strftime('%Y-%m'))['节省费用'].sum()
        save_1.name = '口径2-复测节省'
        # st.dataframe(save_1)

        # st.markdown('---')
        # st.markdown("<hr>", unsafe_allow_html=True)
        # 渐变隔离带
        st.markdown("""
        <div style="
            height: 4px;
            background: linear-gradient(90deg, #ff6b6b, #4ecdc4);
            margin: 25px 0;
            border-radius: 2px;
        "></div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height: 50px;'></div>", unsafe_allow_html=True)

        st.header("📈测试成本节省数据看板")

        # st.divider()
        df3['结束日期'] = pd.to_datetime(df3['结束日期'])
        df3_money0 = df3[['结束日期', '自动化测试节省']].fillna(0)
        df3_money1 = df3[['结束日期', '自有人员测试节省']].fillna(0)

        df3_save0 = df3_money0.groupby(df3_money0['结束日期'].dt.strftime("%Y-%m"))['自动化测试节省'].sum()
        df3_save0.name = '口径3-自动化测试节省'
        df3_save1 = df3_money1.groupby(df3_money1['结束日期'].dt.strftime("%Y-%m"))['自有人员测试节省'].sum()
        df3_save1.name = '口径4-自有人员测试节省'
        # st.dataframe(df3_save1)

        df_save = pd.concat([save_0, save_1, df3_save0, df3_save1], axis=1).fillna(0).sort_index().reset_index()
        df_save_melt = df_save.melt(id_vars='结束日期', var_name='组别', value_name='数值')

        # st.dataframe(df_save_melt)
        df_save['每月节省和'] = df_save.iloc[:, 1:4].sum(axis=1)
        save_total = df_save['每月节省和'].sum()

        st.markdown(
            f"""
                {current_year}测试费用共计节省<span style='color:red; font-size:2.2em'>{save_total:.2f}</span>元，
                口径1节省<span style='color:red; font-size:2.2em'>{df_save['口径1-实际较预估节省'].sum():.2f}</span>元，
                口径2节省<span style='color:red; font-size:2.2em'>{df_save['口径2-复测节省'].sum():.2f}</span>元，
                口径3节省<span style='color:red; font-size:2.2em'>{df_save['口径3-自动化测试节省'].sum()}</span>元，
                口径4节省<span style='color:red; font-size:2.2em'>{df_save['口径4-自有人员测试节省'].sum()}</span>元
            """,
            unsafe_allow_html=True
        )
        st.dataframe(df_save)

        fig_save = px.bar(
            df_save_melt,
            x='结束日期',
            y='数值',
            color='组别',
            barmode='group',
            title='节省费用趋势',
            text_auto='.0f',
            labels={'结束日期': '月份', '数值': '节省金额'}
        )

        # 柱状图与折线图绘制在一张图中
        # fig_save_per_month = px.line(
        #     df_save,
        #     x='结束日期',
        #     y='每月节省和'
        # )
        #
        # fig_save.add_trace(fig_save_per_month.data[0])

        st.plotly_chart(fig_save)




































