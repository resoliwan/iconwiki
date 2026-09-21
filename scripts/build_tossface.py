"""Build a local Tossface SVG catalog from the pinned official release."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import urllib.request
import zipfile


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCES = DATA / "sources"
ASSETS = ROOT / "assets" / "tossface"

VERSION = "1.6.1"
COMMIT = "37720aa5cf2ec9a853a9787f29e39002c58cc2e7"
REPOSITORY_URL = "https://github.com/toss/tossface"
RELEASE_URL = f"{REPOSITORY_URL}/releases/tag/v{VERSION}"
ARCHIVE_URL = f"{REPOSITORY_URL}/releases/download/v{VERSION}/TossFace-Svg.zip"
ARCHIVE_SHA256 = "017deca1e843138d60f9f36d9a6ecf592f59dc6aff6501e8a40ce84482b5a3c7"
ARCHIVE_PREFIX = "TossFace-Svg-v1-6/"
LICENSE_URL = f"https://raw.githubusercontent.com/toss/tossface/{COMMIT}/LICENSE"
LICENSE_SHA256 = "cb3222be7ac066105b35f5b44d4895ae5262bf1492ccfbc1b1e5d0e9db8f7861"
COPYRIGHT_URL = "https://toss.im/tossface/copyright"

EXPECTED_FULLY_QUALIFIED = 3_655
EXPECTED_COMPONENTS = 9
EXPECTED_CATALOG_COUNT = EXPECTED_FULLY_QUALIFIED + EXPECTED_COMPONENTS
EXPECTED_UPSTREAM_ASSET_COUNT = 3_739

CATALOG_PATH = DATA / "tossface.json"
LICENSE_PATH = SOURCES / "TOSSFACE-LICENSE.txt"
NOTICE_PATH = SOURCES / "TOSSFACE-COPYRIGHT-NOTICE.txt"
MANIFEST_PATH = SOURCES / "tossface-manifest.json"

COPYRIGHT_NOTICE = """토스페이스 저작권 안내

공식 원문: https://toss.im/tossface/copyright

1. 토스페이스는 누구나 자유롭게 무료로 이용할 수 있습니다.

토스팀은 모든 사용자에게 토스페이스를 무료로 제공합니다. 단, 아래와 같은 행위는 금지됩니다.

- 토스페이스를 변형ㆍ각색하여 작성한 창작물(이하 “2차적저작물”)을 만드는 행위
- 토스페이스 그 자체를 유료로 판매하는 행위
- 토스페이스 및 이를 활용한 2차적 저작물에 대하여 상표권, 디자인권 등 지식재산권등록을 진행하는 행위
- 토스페이스 및 이를 활용한 2차적 저작물을 전시회 ∙ 공모전에 출품하는 행위
- 토스페이스를 소스코드로 변환하여 이를 복제, 전송, 공중에 게재하는 행위
- 사회 미풍양속을 저해하는 방식으로 토스페이스를 이용하는 행위
- 기타 위와 유사한 행위로서 토스팀의 저작권 및 저작인격권을 침해하는 행위

2. 토스페이스의 권리는 토스팀에게 있습니다.

토스페이스는 토스팀이 직접 창작한 저작물로서 저작권법 등 관계 법령에 따라 보호받고 있는 고유의 지식재산입니다. 따라서 이용하실 때에는 토스페이스가 토스팀의 저작물이라는 출처 표시를 해주세요(저작권법 제12조). 예) 이 페이지에는 토스팀에서 제공한 토스페이스가 적용되어 있습니다.

3. 토스페이스를 이용하여 만들어진 인쇄물, 광고물(온라인 포함) 등의 이미지(이하 ‘이용물들’)는 원칙적으로 당사의 자료 수집, 연구 및 광고 등 프로모션 목적으로 활용될 수 있습니다. 만약 이를 원치 않으실 경우 이용물들 제작 사전에 당사에 요청해 주시기 바랍니다.

4. 본 가이드라인은 토스페이스 사용에 관한 토스팀 정책을 반영하고 있으며 토스페이스 사용에 대한 해석에 가장 우선합니다. 토스페이스의 저작권 관련 원칙 등 기타 궁금하신 사항은 토스페이스 라이선스 전문도 참고하시기 바랍니다.

5. 본 가이드라인은 토스팀 정책 변경에 따라 변경될 수 있으며, 가장 최신의 가이드라인에 따라 이용허락이 제한될 수 있습니다.

위 안내는 2026-09-21 공식 페이지에 게시된 내용을 가독성 있는 텍스트로 보존한 것입니다. 최신 안내는 위 공식 원문을 확인하세요. 공식 라이선스 전문은 TOSSFACE-LICENSE.txt에 별도로 포함되어 있습니다.
"""


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download(url: str) -> bytes:
    request = urllib.request.Request(
        url, headers={"User-Agent": "Moa catalog builder (Tossface attribution)"}
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        return response.read()


def normalized(codepoints: list[str]) -> tuple[str, ...]:
    return tuple(code.upper() for code in codepoints if code.upper() != "FE0F")


def codes_from_filename(filename: str) -> tuple[str, ...] | None:
    stem = Path(filename).stem
    parts = stem.split("_")
    if not parts or any(not part.startswith("u") for part in parts):
        return None
    return tuple(part[1:].upper() for part in parts)


def main() -> None:
    unicode_rows = json.loads((DATA / "unicode.json").read_text(encoding="utf-8"))
    unicode_by_sequence = {normalized(row["codepoints"]): row for row in unicode_rows}

    archive_bytes = download(ARCHIVE_URL)
    archive_digest = sha256_bytes(archive_bytes)
    if archive_digest != ARCHIVE_SHA256:
        raise RuntimeError(
            f"Tossface archive checksum changed: expected {ARCHIVE_SHA256}, got {archive_digest}"
        )

    license_bytes = download(LICENSE_URL)
    license_digest = sha256_bytes(license_bytes)
    if license_digest != LICENSE_SHA256:
        raise RuntimeError(
            f"Tossface license checksum changed: expected {LICENSE_SHA256}, got {license_digest}"
        )

    DATA.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    ASSETS.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="tossface-build-") as temp_name:
        staged = Path(temp_name) / "assets"
        staged.mkdir()
        icons: list[dict[str, object]] = []
        skipped_assets: list[str] = []
        asset_digests: dict[str, str] = {}

        archive_path = Path(temp_name) / "TossFace-Svg.zip"
        archive_path.write_bytes(archive_bytes)
        with zipfile.ZipFile(archive_path) as archive:
            for member in sorted(archive.infolist(), key=lambda entry: entry.filename):
                if member.is_dir() or not member.filename.startswith(ARCHIVE_PREFIX):
                    continue
                if not member.filename.endswith(".svg"):
                    continue

                source_name = Path(member.filename).name
                payload = archive.read(member)
                (staged / source_name).write_bytes(payload)
                asset_digests[source_name] = sha256_bytes(payload)

                codes = codes_from_filename(source_name)
                row = unicode_by_sequence.get(codes) if codes else None
                if row is None:
                    skipped_assets.append(source_name)
                    continue

                codepoints = row["codepoints"]
                slug = "-".join(codepoints)
                item = dict(row)
                item.update(
                    {
                        "id": f"tossface:{slug}",
                        "collection": "tossface",
                        "kind": "image",
                        "src": f"./assets/tossface/{source_name}",
                    }
                )
                icons.append(item)

        status_counts = {
            status: sum(item.get("status") == status for item in icons)
            for status in {item.get("status") for item in icons}
        }
        if status_counts != {
            "fully-qualified": EXPECTED_FULLY_QUALIFIED,
            "component": EXPECTED_COMPONENTS,
        }:
            raise RuntimeError(f"Unexpected Tossface Unicode coverage: {status_counts}")
        if len(icons) != EXPECTED_CATALOG_COUNT:
            raise RuntimeError(
                f"Expected {EXPECTED_CATALOG_COUNT:,} Tossface catalog items, found {len(icons):,}."
            )
        if len(asset_digests) != EXPECTED_UPSTREAM_ASSET_COUNT:
            raise RuntimeError(
                f"Expected {EXPECTED_UPSTREAM_ASSET_COUNT:,} upstream SVG assets, "
                f"found {len(asset_digests):,}."
            )
        if len({item["id"] for item in icons}) != len(icons):
            raise RuntimeError("Duplicate Tossface IDs were generated.")

        catalog_bytes = (
            json.dumps(icons, ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        CATALOG_PATH.write_bytes(catalog_bytes)
        if ASSETS.exists():
            shutil.rmtree(ASSETS)
        staged.replace(ASSETS)

    LICENSE_PATH.write_bytes(license_bytes)
    NOTICE_PATH.write_text(COPYRIGHT_NOTICE, encoding="utf-8")
    manifest = {
        "collection": "tossface",
        "name": "Tossface",
        "version": VERSION,
        "commit": COMMIT,
        "unicodeEmojiVersion": "15.0",
        "sourceUrl": COPYRIGHT_URL,
        "repositoryUrl": REPOSITORY_URL,
        "releaseUrl": RELEASE_URL,
        "archiveUrl": ARCHIVE_URL,
        "archiveSha256": archive_digest,
        "style": "color SVG",
        "assetDirectory": "../../assets/tossface",
        "assetCount": len(asset_digests),
        "catalogItemCount": len(icons),
        "fullyQualifiedCount": EXPECTED_FULLY_QUALIFIED,
        "componentCount": EXPECTED_COMPONENTS,
        "uncataloguedNonRgiOrInternalAssets": len(skipped_assets),
        "assetsSha256": hashlib.sha256(
            "".join(
                f"{name}:{asset_digests[name]}\n" for name in sorted(asset_digests)
            ).encode()
        ).hexdigest(),
        "catalog": "../tossface.json",
        "catalogSha256": sha256_file(CATALOG_PATH),
        "license": "Tossface custom license",
        "licenseUrl": COPYRIGHT_URL,
        "licenseFile": LICENSE_PATH.name,
        "licenseSha256": license_digest,
        "copyrightNoticeFile": NOTICE_PATH.name,
        "copyrightNoticeSha256": sha256_file(NOTICE_PATH),
        "attribution": "Tossface provided by the Toss team.",
        "restrictions": [
            "No modification or derivative works",
            "No sale of Tossface itself",
            "Attribution and the copyright/license notices are required for redistribution",
            "The latest official copyright guide controls",
        ],
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    total_size = sum(path.stat().st_size for path in ASSETS.glob("*.svg"))
    print(
        f"Built {len(icons):,} Tossface catalog entries from "
        f"{len(asset_digests):,} v{VERSION} SVGs ({total_size / 1024 / 1024:.1f} MiB)."
    )


if __name__ == "__main__":
    main()
