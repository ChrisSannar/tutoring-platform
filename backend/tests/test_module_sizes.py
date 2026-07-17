from pathlib import Path


def test_backend_application_modules_stay_under_one_hundred_lines() -> None:
    application_root = Path(__file__).parents[1] / "app"
    oversized = {
        path.relative_to(application_root).as_posix(): len(path.read_text().splitlines())
        for path in application_root.rglob("*.py")
        if len(path.read_text().splitlines()) > 100
    }

    assert oversized == {}, (
        "Split backend application modules over 100 lines along a cohesive domain seam: "
        f"{oversized}"
    )
