
# 缺陷统计求和
def calculate_defect(defect, detail):
    l1 = defect.str.extract(r"一级:(\d+)")  # DataFrame对象
    l2 = defect.str.extract(r"二级:(\d+)")
    l3 = defect.str.extract(r"三级:(\d+)")
    l4 = defect.str.extract(r"四级:(\d+)")
    l5 = defect.str.extract(r"五级:(\d+)")

    pf1 = defect.str.extract(r"未达标:(\d+)")
    pf2 = defect.str.extract(r"达标未达到挑战值:(\d+)")

    ep1 = defect.str.extract(r"高等级:(\d+)")
    ep2 = defect.str.extract(r"中等级:(\d+)")
    ep3 = defect.str.extract(r"低等级:(\d+)")

    l1_sum = l1.iloc[:, 0].fillna(0).astype(int).sum()
    l2_sum = l2.iloc[:, 0].fillna(0).astype(int).sum()
    l3_sum = l3.iloc[:, 0].fillna(0).astype(int).sum()
    l4_sum = l4.iloc[:, 0].fillna(0).astype(int).sum()
    l5_sum = l5.iloc[:, 0].fillna(0).astype(int).sum()

    pf1_sum = pf1.iloc[:, 0].fillna(0).astype(int).sum()
    pf2_sum = pf2.iloc[:, 0].fillna(0).astype(int).sum()

    ep1_sum = ep1.iloc[:, 0].fillna(0).astype(int).sum()
    ep2_sum = ep2.iloc[:, 0].fillna(0).astype(int).sum()
    ep3_sum = ep3.iloc[:, 0].fillna(0).astype(int).sum()

    high_level_defect = l1_sum + l2_sum + l3_sum  # 高等级功能缺陷数（1-3级）
    total_defect = l1_sum + l2_sum + l3_sum + l4_sum + l5_sum + pf1_sum + pf2_sum + ep1_sum + ep2_sum + ep3_sum  # 缺陷总数
    pf_defect = pf1_sum + pf2_sum  # 性能缺陷总数
    ep_defect = ep1_sum + ep2_sum + ep3_sum  # 体验缺陷总数

    if detail == 0:
        return high_level_defect, total_defect, pf_defect, ep_defect
    else:
        return l1, l2, l3, l4, l5, pf1, pf2, ep1, ep2, ep3
