"""Path traversal guards (Issues #306 / #488 / #489).

External IDs (project_id / simulation_id / report_id) and the platform query
parameter are used to build filesystem paths. These tests pin the central
validation layer so traversal payloads can never reach os.path.join.
"""

import pytest

from app.models.project import ProjectManager
from app.services.report_agent import ReportManager
from app.services.simulation_manager import SimulationManager
from app.utils.validation import (
    ensure_platform,
    ensure_safe_id,
    is_allowed_platform,
    is_safe_id,
)

TRAVERSAL_IDS = [
    "../../tmp/pwned",
    "..",
    "../state",
    "a/../../b",
    "a\\..\\..\\b",
    "/etc/passwd",
    "C:\\Windows\\system32",
    "",
    None,
    123,
    ".hidden",
    "-leading-dash",
]

VALID_IDS = [
    "sim_0f6e0b238a42",
    "proj_abc123",
    "report_d831b9a0185c",
    "ABC-123_xyz",
    "a",
]


class TestValidationUtils:
    @pytest.mark.parametrize("bad_id", TRAVERSAL_IDS)
    def test_rejects_traversal_ids(self, bad_id):
        assert not is_safe_id(bad_id)
        with pytest.raises(ValueError):
            ensure_safe_id(bad_id, "simulation_id")

    @pytest.mark.parametrize("good_id", VALID_IDS)
    def test_accepts_internal_id_shapes(self, good_id):
        assert is_safe_id(good_id)
        assert ensure_safe_id(good_id) == good_id

    def test_rejects_overlong_id(self):
        assert not is_safe_id("a" * 65)
        assert is_safe_id("a" * 64)

    def test_platform_whitelist(self):
        assert is_allowed_platform("twitter")
        assert is_allowed_platform("reddit")
        for bad in ("../state", "weibo", "", None, "TWITTER"):
            assert not is_allowed_platform(bad)
            with pytest.raises(ValueError):
                ensure_platform(bad)


class TestPathBuildersRejectTraversal:
    def test_simulation_dir_rejects_traversal(self):
        manager = SimulationManager()
        with pytest.raises(ValueError):
            manager._get_simulation_dir("../../tmp/pwned")

    def test_project_dir_rejects_traversal(self):
        with pytest.raises(ValueError):
            ProjectManager._get_project_dir("../../tmp/pwned")

    def test_report_folder_rejects_traversal(self):
        with pytest.raises(ValueError):
            ReportManager._get_report_folder("../../tmp/pwned")
