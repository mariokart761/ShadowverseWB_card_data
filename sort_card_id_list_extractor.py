import json
from pathlib import Path


def extract_sort_card_id_list(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    result = {
        "sort_card_id_list": data["data"]["sort_card_id_list"]
    }

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"已成功輸出到：{output_path}")


# 範例用法
extract_sort_card_id_list(  
    input_path="./output/shadowverse_cards_cht.json",
    output_path="./output/sort_card_id_list.json"    
)