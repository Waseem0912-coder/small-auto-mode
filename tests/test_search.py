import unittest

from small_auto_mode.search import Tool, search


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.catalog = [
            Tool("mcp__slack__search_messages", "Search Slack messages by keyword"),
            Tool("mcp__slack__send_message", "Send a message to Slack"),
            Tool("mcp__github__search_issues", "Search GitHub issues"),
            Tool("ReadFile", "Read a file", search_hint="documents"),
        ]

    def names(self, query, **kwargs):
        return search(self.catalog, query, **kwargs).as_dict()["matches"]

    def test_exact_name_is_case_insensitive(self):
        self.assertEqual(self.names("READFILE"), ["ReadFile"])

    def test_mcp_prefix_uses_catalog_order_and_limit(self):
        self.assertEqual(self.names("mcp__slack__", max_results=1),
                         ["mcp__slack__search_messages"])

    def test_direct_selection_preserves_order_and_deduplicates(self):
        query = "select:ReadFile,mcp__github__search_issues,ReadFile,missing"
        self.assertEqual(self.names(query, max_results=1),
                         ["ReadFile", "mcp__github__search_issues"])

    def test_direct_select_can_resolve_remote_name(self):
        self.assertEqual(self.names("select:search_issues"),
                         ["mcp__github__search_issues"])

    def test_required_term_excludes_high_scoring_wrong_server(self):
        self.assertEqual(self.names("+github search"),
                         ["mcp__github__search_issues"])

    def test_all_required_terms_must_match(self):
        self.assertEqual(self.names("+github +slack search"), [])

    def test_name_matches_outweigh_description_only(self):
        catalog = [Tool("Unrelated", "search"), Tool("Search")]
        result = search(catalog, "search search")
        self.assertEqual(result.hits[0].name, "Search")
        self.assertEqual(result.hits[0].score, 40)
        self.assertEqual(result.hits[1].score, 4)

    def test_hint_and_description_weights(self):
        result = search([Tool("ReadFile", "documents", "documents")], "documents")
        self.assertEqual(result.hits[0].score, 6)

    def test_description_matches_whole_words(self):
        self.assertEqual(search([Tool("One", "emails")], "mail").hits, ())

    def test_visibility_is_applied_before_direct_select_and_ranking(self):
        visible = {"ReadFile"}
        self.assertEqual(self.names("select:mcp__slack__send_message", allowed_names=visible), [])
        self.assertEqual(self.names("slack", allowed_names=visible), [])
        self.assertEqual(self.names("ReadFile", allowed_names=set()), [])

    def test_api_result_has_only_references(self):
        result = search(self.catalog, "ReadFile").as_tool_result("toolu_test")
        self.assertEqual(result, {"type": "tool_result", "tool_use_id": "toolu_test",
                                  "content": [{"type": "tool_reference", "tool_name": "ReadFile"}]})

    def test_limits_and_duplicate_names_rejected(self):
        for limit in (0, -1, 10001, True, 1.5):
            with self.assertRaises(ValueError):
                search(self.catalog, "slack", limit)
        with self.assertRaises(ValueError):
            search([Tool("same"), Tool("same")], "same")

    def test_query_limits_are_bounded(self):
        self.assertEqual(search([Tool("One", "target")], "noise " * 32 + "target").hits, ())
        result = search([Tool("One", "target")], " " * 16384 + "target")
        self.assertEqual(result.hits, ())
        self.assertEqual(len(result.query), 16384)

    def test_stable_ties(self):
        catalog = [Tool("B", "keyword"), Tool("A", "keyword")]
        self.assertEqual([hit.name for hit in search(catalog, "keyword").hits], ["B", "A"])

    def test_catalog_loading(self):
        tool = Tool.from_dict({"name": "opaque", "mcp_info": {
            "server_name": "slack", "tool_name": "send_message"}})
        self.assertEqual(search([tool], "+slack message").hits[0].name, "opaque")
        with self.assertRaises(ValueError):
            Tool.from_dict({"name": 3})


if __name__ == "__main__":
    unittest.main()
