#!/usr/bin/env python3
"""
Shadowverse 卡片資料同步至 Supabase 腳本 - 優化版本

主要優化：
1. 使用批次 upsert 取代逐筆 select + insert/update。
2. 將 card_bases、card_i18n、card_texts、tips 等表批次寫入。
3. 將 card_tribes、card_relations、card_questions 改為批次刪除 + 批次新增。
4. 權限檢查只在同步流程開始時執行一次，避免每個語言重複檢查。
5. 保留原本 CLI 介面與資料檔案路徑。

注意：
- 需要相關資料表有唯一約束，才能正確 upsert：
  card_set_bases(id)
  card_set_i18n(card_set_id, language)
  tribe_bases(id)
  tribe_i18n(tribe_id, language)
  skill_bases(id)
  skill_i18n(skill_id, language)
  card_bases(card_id)
  card_i18n(card_id, language)
  card_texts(card_id, language)
- service_role key 建議只在可信任的後端或本機腳本中使用。
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from supabase import Client, create_client
except ImportError:
    print("請先安裝 supabase-py: pip install supabase")
    sys.exit(1)


class ShadowverseDataSync:
    def __init__(self):
        """初始化同步器"""
        self.supabase: Optional[Client] = None
        self.schema_name = "public"
        self.batch_size = 500
        self.permissions_checked = False
        self.load_config()

    def load_config(self):
        """從配置文件載入 Supabase 連線資訊"""
        config_path = Path("supabase/config.json")

        if not config_path.exists():
            print(f"配置文件不存在: {config_path}")
            print("請創建配置文件，格式如下:")
            print(
                """
{
    "supabase_url": "https://your-project.supabase.co",
    "supabase_key": "your-service-role-key"
}
                """.strip()
            )
            sys.exit(1)

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)

            required_keys = ["supabase_url", "supabase_key"]
            for key in required_keys:
                if key not in config:
                    print(f"配置文件缺少必要參數: {key}")
                    sys.exit(1)

            self.supabase = create_client(config["supabase_url"], config["supabase_key"])
            print(f"✓ 成功連接到 Supabase: {config['supabase_url']}")

        except json.JSONDecodeError as e:
            print(f"配置文件格式錯誤: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"載入配置失敗: {e}")
            sys.exit(1)

    def _get_table(self, table_name: str):
        """獲取指定 schema 的表引用"""
        if self.supabase is None:
            raise RuntimeError("Supabase client 尚未初始化")
        return self.supabase.schema(self.schema_name).table(table_name)

    def _chunked(self, items: Sequence[Any], size: Optional[int] = None) -> Iterable[Sequence[Any]]:
        """將資料切成批次，避免單次 request 過大"""
        batch_size = size or self.batch_size
        for i in range(0, len(items), batch_size):
            yield items[i : i + batch_size]

    def _safe_execute(self, label: str, fn):
        """統一處理 execute 錯誤，讓錯誤訊息更清楚"""
        try:
            return fn()
        except Exception as e:
            print(f"    ✗ {label} 失敗: {e}")
            raise

    def _bulk_upsert(
        self,
        table_name: str,
        rows: List[Dict[str, Any]],
        on_conflict: str,
        label: str,
        ignore_duplicates: bool = False,
    ):
        """批次 upsert"""
        if not rows:
            return

        total = len(rows)
        for batch in self._chunked(rows):
            self._safe_execute(
                f"{label} upsert {len(batch)}/{total}",
                lambda batch=batch: self._get_table(table_name)
                .upsert(
                    list(batch),
                    on_conflict=on_conflict,
                    ignore_duplicates=ignore_duplicates,
                )
                .execute(),
            )

    def _bulk_insert(self, table_name: str, rows: List[Dict[str, Any]], label: str):
        """批次 insert"""
        if not rows:
            return

        total = len(rows)
        for batch in self._chunked(rows):
            self._safe_execute(
                f"{label} insert {len(batch)}/{total}",
                lambda batch=batch: self._get_table(table_name).insert(list(batch)).execute(),
            )

    def _bulk_delete_by_language(self, table_name: str, language_code: str, label: str):
        """依語言刪除資料"""
        self._safe_execute(
            f"刪除 {label}",
            lambda: self._get_table(table_name).delete().eq("language", language_code).execute(),
        )

    def _bulk_delete_by_card_ids(self, table_name: str, card_ids: List[int], label: str):
        """依 card_id 批次刪除資料"""
        if not card_ids:
            return

        unique_card_ids = sorted(set(card_ids))
        for batch in self._chunked(unique_card_ids):
            self._safe_execute(
                f"刪除 {label} {len(batch)}/{len(unique_card_ids)}",
                lambda batch=batch: self._get_table(table_name)
                .delete()
                .in_("card_id", list(batch))
                .execute(),
            )

    def _check_permissions(self, force: bool = False) -> bool:
        """檢查資料庫權限。預設只檢查一次。"""
        if self.permissions_checked and not force:
            return True

        try:
            print("\n檢查資料庫權限...")
            test_tables: List[Tuple[str, str]] = [
                ("card_set_bases", "id"),
                ("card_set_i18n", "card_set_id"),
                ("tribe_bases", "id"),
                ("tribe_i18n", "tribe_id"),
                ("skill_bases", "id"),
                ("skill_i18n", "skill_id"),
                ("card_bases", "card_id"),
                ("card_i18n", "card_id"),
                ("card_texts", "id"),
                ("card_tribes", "id"),
                ("card_relations", "id"),
                ("card_questions", "id"),
                ("tips", "id"),
            ]

            for table, col in test_tables:
                try:
                    self._get_table(table).select(col).limit(1).execute()
                    print(f"    ✓ {table} 權限檢查通過")
                except Exception as e:
                    error_msg = str(e)
                    if "permission denied" in error_msg.lower():
                        print(f"    ✗ {table} 權限檢查失敗: {error_msg}")
                        return False
                    print(f"    ⚠ {table} 權限檢查遇到錯誤: {error_msg}")

            self.permissions_checked = True
            return True

        except Exception as e:
            print(f"    ✗ 權限檢查失敗: {e}")
            return False

    def sync_card_data(self, language_code: str, skip_permission_check: bool = False):
        """同步卡片資料"""
        card_file_path = Path(f"output/shadowverse_cards_{language_code}.json")

        if not card_file_path.exists():
            print(f"卡片資料文件不存在: {card_file_path}")
            return False

        try:
            with open(card_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(f"\n開始同步 {language_code} 語言卡片資料...")

            if not skip_permission_check and not self._check_permissions():
                print(f"✗ {language_code} 語言卡片資料同步失敗: 權限檢查未通過")
                return False

            payload = data.get("data", {})

            self._sync_card_sets(payload.get("card_set_names", {}), language_code)
            self._sync_tribes(payload.get("tribe_names", {}), language_code)
            self._sync_skills(
                payload.get("skill_names", {}),
                payload.get("skill_replace_text_names", {}),
                language_code,
            )

            self._sync_cards(
                payload.get("card_details", {}),
                payload.get("cards", {}),
                language_code,
            )

            print(f"✓ {language_code} 語言卡片資料同步完成")
            return True

        except Exception as e:
            error_msg = str(e)
            if "permission denied" in error_msg.lower():
                print(f"✗ 同步 {language_code} 語言卡片資料失敗: 權限不足 - {error_msg}")
                print("💡 請確認已應用最新的 schema.sql 並重新啟動資料庫連線")
            else:
                print(f"✗ 同步 {language_code} 語言卡片資料失敗: {e}")
            return False

    def _sync_card_sets(self, card_sets: Dict[str, str], language_code: str):
        """同步卡組系列資料"""
        if not card_sets:
            return

        print("  同步卡組系列資料...")
        base_rows: List[Dict[str, Any]] = []
        i18n_rows: List[Dict[str, Any]] = []

        for set_id, set_name in card_sets.items():
            set_id_int = int(set_id)
            base_rows.append({"id": set_id_int})
            i18n_rows.append(
                {
                    "card_set_id": set_id_int,
                    "language": language_code,
                    "name": set_name,
                }
            )

        self._bulk_upsert("card_set_bases", base_rows, "id", "卡組基礎資料")
        self._bulk_upsert("card_set_i18n", i18n_rows, "card_set_id,language", "卡組多語資料")

    def _sync_tribes(self, tribes: Dict[str, str], language_code: str):
        """同步部族資料"""
        if not tribes:
            return

        print("  同步部族資料...")
        base_rows: List[Dict[str, Any]] = []
        i18n_rows: List[Dict[str, Any]] = []

        for tribe_id, tribe_name in tribes.items():
            tribe_id_int = int(tribe_id)
            base_rows.append({"id": tribe_id_int})
            i18n_rows.append(
                {
                    "tribe_id": tribe_id_int,
                    "language": language_code,
                    "name": tribe_name,
                }
            )

        self._bulk_upsert("tribe_bases", base_rows, "id", "部族基礎資料")
        self._bulk_upsert("tribe_i18n", i18n_rows, "tribe_id,language", "部族多語資料")

    def _sync_skills(self, skills: Dict[str, str], skill_replace_texts: Dict[str, str], language_code: str):
        """同步技能資料"""
        if not skills:
            return

        print("  同步技能資料...")
        base_rows: List[Dict[str, Any]] = []
        i18n_rows: List[Dict[str, Any]] = []

        for skill_id, skill_name in skills.items():
            skill_id_int = int(skill_id)
            base_rows.append({"id": skill_id_int})
            i18n_rows.append(
                {
                    "skill_id": skill_id_int,
                    "language": language_code,
                    "name": skill_name,
                    "replace_text": skill_replace_texts.get(skill_id, ""),
                }
            )

        self._bulk_upsert("skill_bases", base_rows, "id", "技能基礎資料")
        self._bulk_upsert("skill_i18n", i18n_rows, "skill_id,language", "技能多語資料")

    def _sync_cards(self, card_details: Dict[str, Any], cards_data: Dict[str, Any], language_code: str):
        """同步卡片資料"""
        if not card_details:
            return

        print(f"  同步卡片資料... (共 {len(card_details)} 張)")

        base_rows: List[Dict[str, Any]] = []
        i18n_rows: List[Dict[str, Any]] = []
        text_rows: List[Dict[str, Any]] = []
        tribe_rows: List[Dict[str, Any]] = []
        relation_rows: List[Dict[str, Any]] = []
        question_rows: List[Dict[str, Any]] = []
        card_ids: List[int] = []
        processed = 0

        for card_id, card_info in card_details.items():
            try:
                card_id_int = int(card_id)
                common = card_info.get("common", {})
                evo = card_info.get("evo", {}) or {}

                if not common:
                    continue

                real_card_id = int(common.get("card_id", card_id_int))
                card_ids.append(real_card_id)

                base_rows.append(
                    {
                        "card_id": real_card_id,
                        "base_card_id": common.get("base_card_id", real_card_id),
                        "atk": common.get("atk"),
                        "life": common.get("life"),
                        "cost": common.get("cost", 0),
                        "type": common.get("type", 1),
                        "class": common.get("class", 0),
                        "rarity": common.get("rarity", 1),
                        "card_set_id": common.get("card_set_id"),
                        "is_token": common.get("is_token", False),
                        "is_include_rotation": common.get("is_include_rotation", True),
                    }
                )

                i18n_rows.append(
                    {
                        "card_id": real_card_id,
                        "language": language_code,
                        "name": common.get("name", ""),
                        "name_ruby": common.get("name_ruby", ""),
                        "cv": common.get("cv", ""),
                        "illustrator": common.get("illustrator", ""),
                        "card_resource_id": common.get("card_resource_id"),
                        "card_image_hash": common.get("card_image_hash", ""),
                        "card_banner_image_hash": common.get("card_banner_image_hash", ""),
                        "evo_card_resource_id": evo.get("card_resource_id"),
                        "evo_card_image_hash": evo.get("card_image_hash", ""),
                        "evo_card_banner_image_hash": evo.get("card_banner_image_hash", ""),
                    }
                )

                text_rows.append(
                    {
                        "card_id": real_card_id,
                        "language": language_code,
                        "skill_text": common.get("skill_text", ""),
                        "flavour_text": common.get("flavour_text", ""),
                        "evo_skill_text": evo.get("skill_text", ""),
                        "evo_flavour_text": evo.get("flavour_text", ""),
                    }
                )

                if language_code == "cht":
                    tribe_rows.extend(self._build_card_tribe_rows(real_card_id, common.get("tribes", [])))
                    relation_rows.extend(self._build_card_relation_rows(real_card_id, cards_data.get(card_id, {})))

                questions = common.get("questions", [])
                if questions:
                    question_rows.extend(self._build_card_question_rows(real_card_id, questions, language_code))

                processed += 1
                if processed % 500 == 0:
                    print(f"    已整理 {processed}/{len(card_details)} 張卡片")

            except Exception as e:
                print(f"    ✗ 整理卡片 {card_id} 失敗: {e}")

        print("    寫入卡片基礎資料...")
        self._bulk_upsert("card_bases", base_rows, "card_id", "卡片基礎資料")

        print("    寫入卡片多語資料...")
        self._bulk_upsert("card_i18n", i18n_rows, "card_id,language", "卡片多語資料")

        print("    寫入卡片文字資料...")
        self._bulk_upsert("card_texts", text_rows, "card_id,language", "卡片文字資料")

        if language_code == "cht":
            print("    同步卡片部族關係...")
            self._bulk_delete_by_card_ids("card_tribes", card_ids, "卡片部族關係")
            self._bulk_insert("card_tribes", tribe_rows, "卡片部族關係")

            print("    同步相關卡片關係...")
            self._bulk_delete_by_card_ids("card_relations", card_ids, "相關卡片關係")
            self._bulk_insert("card_relations", relation_rows, "相關卡片關係")

        print("    同步卡片問答...")
        self._delete_card_questions_by_language_and_card_ids(card_ids, language_code)
        self._bulk_insert("card_questions", question_rows, "卡片問答")

        print(f"    ✓ 完成處理 {processed} 張卡片")

    def _build_card_tribe_rows(self, card_id: int, tribes: List[int]) -> List[Dict[str, Any]]:
        """建立卡片部族關係 rows"""
        rows: List[Dict[str, Any]] = []
        for tribe_id in tribes or []:
            try:
                tribe_id_int = int(tribe_id)
                if tribe_id_int > 0:
                    rows.append({"card_id": card_id, "tribe_id": tribe_id_int})
            except (TypeError, ValueError):
                continue
        return rows

    def _build_card_relation_rows(self, card_id: int, relations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """建立卡片關係 rows"""
        rows: List[Dict[str, Any]] = []

        for related_id in relations.get("related_card_ids", []) or []:
            rows.append(
                {
                    "card_id": card_id,
                    "related_card_id": related_id,
                    "relation_type": "related",
                }
            )

        for effect_id in relations.get("specific_effect_card_ids", []) or []:
            rows.append(
                {
                    "card_id": card_id,
                    "related_card_id": effect_id,
                    "relation_type": "specific_effect",
                }
            )

        return rows

    def _build_card_question_rows(
        self,
        card_id: int,
        questions: List[Dict[str, Any]],
        language_code: str,
    ) -> List[Dict[str, Any]]:
        """建立卡片問答 rows"""
        rows: List[Dict[str, Any]] = []
        for qa in questions or []:
            rows.append(
                {
                    "card_id": card_id,
                    "language": language_code,
                    "question": qa.get("question", ""),
                    "answer": qa.get("answer", ""),
                }
            )
        return rows

    def _delete_card_questions_by_language_and_card_ids(self, card_ids: List[int], language_code: str):
        """依 card_id 與 language 批次刪除問答"""
        if not card_ids:
            return

        unique_card_ids = sorted(set(card_ids))
        for batch in self._chunked(unique_card_ids):
            self._safe_execute(
                f"刪除卡片問答 {len(batch)}/{len(unique_card_ids)}",
                lambda batch=batch: self._get_table("card_questions")
                .delete()
                .eq("language", language_code)
                .in_("card_id", list(batch))
                .execute(),
            )

    def sync_tips_data(self, language_code: str, skip_permission_check: bool = False):
        """同步提示資料"""
        tips_file_path = Path(f"output/tips_data/tips_data_{language_code}.json")

        if not tips_file_path.exists():
            print(f"提示資料文件不存在: {tips_file_path}")
            return False

        try:
            with open(tips_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(f"\n開始同步 {language_code} 語言提示資料...")

            if not skip_permission_check and not self._check_permissions():
                print(f"✗ {language_code} 語言提示資料同步失敗: 權限檢查未通過")
                return False

            tips = data.get("tips", [])
            if not tips:
                print("  無提示資料")
                return True

            rows = [
                {
                    "language": language_code,
                    "title": tip.get("title", ""),
                    "description": tip.get("desc", ""),
                    "sort_order": i + 1,
                }
                for i, tip in enumerate(tips)
            ]

            self._bulk_delete_by_language("tips", language_code, f"{language_code} 提示資料")
            self._bulk_insert("tips", rows, f"{language_code} 提示資料")

            print(f"✓ {language_code} 語言提示資料同步完成 (共 {len(tips)} 條)")
            return True

        except Exception as e:
            error_msg = str(e)
            if "permission denied" in error_msg.lower():
                print(f"✗ 同步 {language_code} 語言提示資料失敗: 權限不足 - {error_msg}")
                print("💡 請確認已應用最新的 schema.sql 並重新啟動資料庫連線")
            else:
                print(f"✗ 同步 {language_code} 語言提示資料失敗: {e}")
            return False

    def sync_all_languages(self, languages: Optional[List[str]] = None):
        """同步所有語言的資料"""
        if languages is None:
            languages = ["cht", "chs", "en", "ja", "ko"]

        print("=== 開始同步 Shadowverse 資料到 Supabase ===")

        if not self._check_permissions():
            print("✗ 權限檢查未通過，停止同步")
            return False

        success_count = 0
        total_count = len(languages) * 2

        for lang in languages:
            print(f"\n--- 處理 {lang.upper()} 語言 ---")

            if self.sync_card_data(lang, skip_permission_check=True):
                success_count += 1

            if self.sync_tips_data(lang, skip_permission_check=True):
                success_count += 1

        print("\n=== 同步完成 ===")
        print(f"成功: {success_count}/{total_count}")

        if success_count == total_count:
            print("✓ 所有資料同步成功")
            return True

        print(f"✗ {total_count - success_count} 項同步失敗")
        return False

    def validate_data_integrity(self):
        """驗證資料完整性"""
        print("\n=== 驗證資料完整性 ===")

        try:
            languages = ["cht", "chs", "en", "ja", "ko"]
            total_cards = 0

            for lang in languages:
                cards_result = self._get_table("card_i18n").select("card_id").eq("language", lang).execute()
                texts_result = self._get_table("card_texts").select("id").eq("language", lang).execute()
                tips_result = self._get_table("tips").select("id").eq("language", lang).execute()
                card_sets_result = self._get_table("card_set_i18n").select("card_set_id").eq("language", lang).execute()
                tribes_result = self._get_table("tribe_i18n").select("tribe_id").eq("language", lang).execute()
                skills_result = self._get_table("skill_i18n").select("skill_id").eq("language", lang).execute()
                questions_result = self._get_table("card_questions").select("id").eq("language", lang).execute()

                cards_count = len(cards_result.data or [])
                total_cards += cards_count

                print(f"{lang.upper()} - 卡片: {cards_count}, 卡片文字: {len(texts_result.data or [])}, 提示: {len(tips_result.data or [])}")
                print(
                    f"        卡組: {len(card_sets_result.data or [])}, "
                    f"部族: {len(tribes_result.data or [])}, "
                    f"技能: {len(skills_result.data or [])}, "
                    f"問答: {len(questions_result.data or [])}"
                )

            print(f"總卡片數: {total_cards}")

            base_cards_result = self._get_table("card_bases").select("card_id").execute()
            base_card_sets_result = self._get_table("card_set_bases").select("id").execute()
            base_tribes_result = self._get_table("tribe_bases").select("id").execute()
            base_skills_result = self._get_table("skill_bases").select("id").execute()

            print(
                "基礎表 - "
                f"卡片: {len(base_cards_result.data or [])}, "
                f"卡組: {len(base_card_sets_result.data or [])}, "
                f"部族: {len(base_tribes_result.data or [])}, "
                f"技能: {len(base_skills_result.data or [])}"
            )

            tribes_relations_result = self._get_table("card_tribes").select("id").execute()
            card_relations_result = self._get_table("card_relations").select("id").execute()
            all_questions_result = self._get_table("card_questions").select("id").execute()

            print(f"部族關係: {len(tribes_relations_result.data or [])}")
            print(f"卡片關係: {len(card_relations_result.data or [])}")
            print(f"問答: {len(all_questions_result.data or [])}")

            print("✓ 資料完整性檢查完成")
            return True

        except Exception as e:
            print(f"✗ 資料完整性檢查失敗: {e}")
            return False

    def clean_database(self):
        """清理資料庫（警告：會刪除所有資料）"""
        print("\n=== 清理資料庫 ===")

        confirm = input("⚠️  這將刪除所有同步的資料，確定要繼續嗎？(yes/no): ")
        if confirm.lower() != "yes":
            print("操作已取消")
            return False

        try:
            tables_to_clean = [
                "card_questions",
                "card_relations",
                "card_tribes",
                "card_texts",
                "card_i18n",
                "card_set_i18n",
                "tribe_i18n",
                "skill_i18n",
                "card_bases",
                "card_set_bases",
                "tribe_bases",
                "skill_bases",
                "tips",
            ]

            for table in tables_to_clean:
                try:
                    self._get_table(table).delete().gte("created_at", "1970-01-01").execute()
                    print(f"✓ 已清理 {table}")
                except Exception as e:
                    print(f"✗ 清理 {table} 失敗: {e}")

            print("✓ 資料庫清理完成")
            return True

        except Exception as e:
            print(f"✗ 資料庫清理失敗: {e}")
            return False

    def test_connection(self):
        """測試 Supabase 連線和 schema 存取"""
        print("\n=== 測試連線和 schema 存取 ===")

        try:
            test_tables = [
                ("card_set_bases", "id"),
                ("card_set_i18n", "card_set_id"),
                ("tribe_bases", "id"),
                ("tribe_i18n", "tribe_id"),
                ("skill_bases", "id"),
                ("skill_i18n", "skill_id"),
                ("card_bases", "card_id"),
                ("card_i18n", "card_id"),
                ("card_texts", "id"),
                ("card_tribes", "id"),
                ("card_relations", "id"),
                ("card_questions", "id"),
                ("tips", "id"),
            ]

            for table, test_col in test_tables:
                try:
                    self._get_table(table).select(test_col).limit(1).execute()
                    print(f"✓ 成功存取 {self.schema_name}.{table}")
                except Exception as e:
                    print(f"✗ 無法存取 {self.schema_name}.{table}: {e}")

            return True

        except Exception as e:
            print(f"✗ 連線測試失敗: {e}")
            print("\n可能的解決方案:")
            print("1. 確認 public schema 可存取")
            print("2. 確認使用的是 service_role key 而非 anon key")
            print("3. 確認 RLS 政策已正確設置")
            print("4. 確認已應用最新的 schema.sql（包含 base + i18n 表結構）")
            return False


def main():
    """主程式"""
    import argparse

    parser = argparse.ArgumentParser(description="同步 Shadowverse 資料到 Supabase")
    parser.add_argument(
        "--languages",
        "-l",
        nargs="+",
        default=["cht", "chs", "en", "ja", "ko"],
        help="要同步的語言代碼 (預設: cht chs en ja ko)",
    )
    parser.add_argument("--cards-only", action="store_true", help="只同步卡片資料")
    parser.add_argument("--tips-only", action="store_true", help="只同步提示資料")
    parser.add_argument("--validate", action="store_true", help="驗證資料完整性")
    parser.add_argument("--clean", action="store_true", help="清理資料庫（危險操作）")
    parser.add_argument("--test", action="store_true", help="測試連線和 schema 存取")
    parser.add_argument("--batch-size", type=int, default=500, help="批次寫入大小，預設 500")

    args = parser.parse_args()

    sync = ShadowverseDataSync()
    sync.batch_size = max(1, args.batch_size)

    try:
        if args.test:
            sync.test_connection()
        elif args.clean:
            sync.clean_database()
        elif args.validate:
            sync.validate_data_integrity()
        elif args.cards_only:
            if not sync._check_permissions():
                print("✗ 權限檢查未通過，停止同步")
                sys.exit(1)

            success_count = 0
            for lang in args.languages:
                if sync.sync_card_data(lang, skip_permission_check=True):
                    success_count += 1
            print(f"\n卡片資料同步完成: {success_count}/{len(args.languages)} 成功")
        elif args.tips_only:
            if not sync._check_permissions():
                print("✗ 權限檢查未通過，停止同步")
                sys.exit(1)

            success_count = 0
            for lang in args.languages:
                if sync.sync_tips_data(lang, skip_permission_check=True):
                    success_count += 1
            print(f"\n提示資料同步完成: {success_count}/{len(args.languages)} 成功")
        else:
            success = sync.sync_all_languages(args.languages)
            if success:
                print("\n自動驗證資料完整性...")
                sync.validate_data_integrity()

    except KeyboardInterrupt:
        print("\n\n操作被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ 程式執行失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
