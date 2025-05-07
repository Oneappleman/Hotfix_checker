import streamlit as st
import pandas as pd
from io import BytesIO

st.title("🔍 Сверка дистрибутивов и веток Hotfix")

# --- Вспомогательные функции ---

def extract_component_from_branch(branch_path: str) -> str:
    """
    Извлекает наименование компонента из пути ветки, например:
    modules/rskp/rskp-monitoring-front/hotfix/2.1.2 → rskp-monitoring-front
    """
    parts = branch_path.strip().split('/')
    for part in reversed(parts):
        if "-" in part:
            return part
    return parts[-1] if parts else branch_path.strip()

def extract_component_from_distribution(dist_line: str) -> str:
    """
    Извлекает наименование компонента из строки дистрибутива:
    rskp-monitoring-front: hotfix_2.1.2-xxxx → rskp-monitoring-front
    """
    return dist_line.strip().split(":")[0].strip()

def to_excel(df):
    """Конвертирует DataFrame в Excel для скачивания."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

def load_mapping_from_file(uploaded_file):
    """Загружает Excel-файл с маппингом."""
    try:
        return pd.read_excel(uploaded_file, engine="openpyxl")
    except Exception as e:
        st.error(f"Ошибка при загрузке файла: {e}")
        return pd.DataFrame(columns=["Компонент", "Дистрибутив"])

# --- Загрузка данных ---

branches_input = st.text_area("Вставьте список веток (по одной на строку):")
dists_input = st.text_area("Вставьте список установленных дистрибутивов (по одной на строку):")

uploaded_file = st.file_uploader("Загрузите Excel-файл с маппингом (2 колонки: Компонент, Дистрибутив)", type=["xlsx"])

# --- Основная логика ---

if uploaded_file:
    mapping_df = load_mapping_from_file(uploaded_file)
    st.session_state.mapping_df = mapping_df  # сохраняем в сессию

    branch_list = [line for line in branches_input.strip().splitlines() if line]
    dist_list = [line for line in dists_input.strip().splitlines() if line]

    branch_components = [extract_component_from_branch(b) for b in branch_list]
    distribution_components = [extract_component_from_distribution(d) for d in dist_list]

    mapping_dict = dict(zip(mapping_df["Компонент"], mapping_df["Дистрибутив"]))

    missing_distributions = []
    unmapped_branches = []
    unmapped_distributions = []
    checked_components = []

    for comp in branch_components:
        if comp not in mapping_dict:
            unmapped_branches.append(comp)
        else:
            expected_dist = mapping_dict[comp]
            checked_components.append(comp)
            if expected_dist not in distribution_components:
                missing_distributions.append(expected_dist)

    for dist in distribution_components:
        if dist not in mapping_dict.values():
            unmapped_distributions.append(dist)

    if st.button("🧪 Сверка"):
        if missing_distributions:
            st.warning("⚠️ Проблема: отсутствуют дистрибутивы по следующим веткам:")
            st.code("\n".join(missing_distributions))
        else:
            st.success("✅ Всё ОК! Все доступные дистрибутивы по веткам установлены.")

        if unmapped_branches or unmapped_distributions:
            st.error("❌ Внимание! Есть элементы, не учтённые в маппинге.")
            if unmapped_branches:
                st.write("🔸 Неучтённые компоненты из веток:")
                st.code("\n".join(unmapped_branches))
            if unmapped_distributions:
                st.write("🔸 Неучтённые дистрибутивы:")
                st.code("\n".join(unmapped_distributions))

        # Показываем таблицу сопоставлений
        st.write("📋 Использованный маппинг:")
        st.dataframe(mapping_df)

        # Кнопка для скачивания текущего маппинга
        st.download_button(
            "⬇️ Скачать маппинг в Excel",
            data=to_excel(mapping_df),
            file_name="mapping_hotfix.xlsx"
        )
