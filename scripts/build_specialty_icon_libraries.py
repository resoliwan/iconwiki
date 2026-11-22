"""Build the specialty collections from pinned Iconify packages and license texts."""

from build_recommended_icon_libraries import build, iconify_source


LIBRARIES = {
    "fontaudio": {
        "name": "FontAudio", "version": "1.2.1", "group": "Audio",
        "upstream": "https://github.com/fefanto/fontaudio",
        "license": "CC-BY-4.0", "license_class": "attribution", "license_file": "FONTAUDIO-LICENSE.txt",
        "sources": [iconify_source("@iconify-json/fad", "1.2.1", "c134ecc14f3765679ba6d4112d30e7b6d0e5c6e490fa1d7f4abe1da87054bd47", 155)],
        "license_sources": [{
            "file": "FONTAUDIO-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/spdx/license-list-data/ab9b0904b43db6f4b67431efd8821feb821f1c8b/text/CC-BY-4.0.txt",
            "sha256": "d557539df68e771cc1eedcc91d13f70fca930e508d11eedcafa4b15db49e3744",
        }],
        "note": "FontAudio by Michelangelo Nottoli (@fefanto). SVG artwork is licensed under CC BY 4.0 and normalized by Iconify.",
    },
    "font-gis": {
        "name": "Font-GIS", "version": "1.2.6", "group": "Maps",
        "upstream": "https://github.com/viglino/font-gis",
        "license": "CC-BY-4.0", "license_class": "attribution", "license_file": "FONT-GIS-LICENSE.txt",
        "sources": [iconify_source("@iconify-json/gis", "1.2.6", "ef7288f72fe575b911be6393cd13a553ed580a7a7b25846b5cb24e95c4af88f6", 367)],
        "license_sources": [{
            "file": "FONT-GIS-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/viglino/font-gis/c3b99d144cf2feefa65fc2e0167c167d7bc27bac/LICENSE-CC-BY.md",
            "sha256": "52558ccee18aba16bea0dd1607386e1b3304b501d9e3be61b36f3a7843781c73",
        }],
        "note": "Font-GIS mapping symbols by Jean-Marc Viglino, normalized by Iconify under CC BY 4.0.",
    },
    "academicons": {
        "name": "Academicons", "version": "1.2.4", "group": "Academic",
        "upstream": "https://github.com/jpswalsh/academicons",
        "license": "OFL-1.1", "license_class": "permissive", "license_file": "ACADEMICONS-LICENSE.txt",
        "sources": [iconify_source("@iconify-json/academicons", "1.2.4", "f758417f3500122c31aaa5fea7a20bd777d72d0105cf871136fddc39e930b6d3", 158)],
        "license_sources": [{
            "file": "ACADEMICONS-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/spdx/license-list-data/ab9b0904b43db6f4b67431efd8821feb821f1c8b/text/OFL-1.1.txt",
            "sha256": "8eea8287e5876b539670cadb82e99f9a7afddec6f6730811be1daf25d2e9bcfd",
        }],
        "style_suffixes": [("-square", "square")],
        "note": "Academic service logos from the Academicons font by James Walsh, normalized by Iconify under the SIL Open Font License 1.1.",
    },
    "svg-spinners": {
        "name": "SVG Spinners", "version": "1.2.4", "group": "Loading",
        "upstream": "https://github.com/n3r4zzurr0/svg-spinners",
        "license": "MIT", "license_class": "permissive", "license_file": "SVG-SPINNERS-LICENSE.txt",
        "sources": [iconify_source("@iconify-json/svg-spinners", "1.2.4", "243a55ead4c8e3a5d125afc32ed54c3eb3e50e0e0eec24e5f98d616ed1267b5c", 46)],
        "license_sources": [{
            "file": "SVG-SPINNERS-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/n3r4zzurr0/svg-spinners/abfa05c49acf005b8b1e0ef8eb25a67a7057eb20/LICENSE",
            "sha256": "712f8f614e9a23cc754a21d72ea443f1166077e4ee0e6c3b6f9fa576a6d37254",
        }],
        "note": "Animated SVG loading indicators by Utkarsh Verma.",
    },
    "material-icon-theme": {
        "name": "Material Icon Theme", "version": "1.2.77", "group": "Development",
        "upstream": "https://github.com/material-extensions/vscode-material-icon-theme",
        "license": "MIT", "license_class": "permissive", "license_file": "MATERIAL-ICON-THEME-LICENSE.txt",
        "sources": [iconify_source("@iconify-json/material-icon-theme", "1.2.77", "0d8a33a72f31e9a5adc35424cf5eada50ea8e27d760fef8cf7e1d028a282ebd7", 910)],
        "license_sources": [{
            "file": "MATERIAL-ICON-THEME-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/material-extensions/vscode-material-icon-theme/8e461d1e48b0e66f1927d074e58f09135933dd39/LICENSE",
            "sha256": "cdab3014d4f69b49dde2b85e81792208c72de613aa6aed7f7a9b5c6609b89670",
        }],
        "style_suffixes": [("-light", "light")],
        "note": "File and folder icons from the Material Icon Theme for Visual Studio Code.",
    },
    "temaki": {
        "name": "Temaki", "version": "1.2.7", "group": "Maps",
        "upstream": "https://github.com/rapideditor/temaki",
        "license": "CC0-1.0", "license_class": "permissive", "license_file": "TEMAKI-LICENSE.txt",
        "sources": [iconify_source("@iconify-json/temaki", "1.2.7", "ee5bc3b129ba9312181ff9e3e2995eb213147d5479c95afa9dd56fecfc554d74", 557)],
        "license_sources": [{
            "file": "TEMAKI-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/rapideditor/temaki/f2bb5387ae32d54aefc370959caf5e3ba783930c/LICENSE.md",
            "sha256": "32e9b76c6886b3b17c7a96ec0fbe6fb96b7ebf41cdd1f344f28b748631f95b8b",
        }],
        "note": "Point-of-interest mapping symbols by Bryan Housel and the Temaki contributors.",
    },
    "arcticons": {
        "name": "Arcticons", "version": "1.2.62", "group": "Apps",
        "upstream": "https://github.com/Arcticons-Team/Arcticons",
        "license": "CC-BY-SA-4.0", "license_class": "attribution", "license_file": "ARCTICONS-LICENSE.txt",
        "sources": [iconify_source("@iconify-json/arcticons", "1.2.62", "ce979b788134186bf7fe6d32cc2eb707dc54a0bf6a53c63f3b749c683c74cc60", 15457)],
        "license_sources": [{
            "file": "ARCTICONS-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/spdx/license-list-data/ab9b0904b43db6f4b67431efd8821feb821f1c8b/text/CC-BY-SA-4.0.txt",
            "sha256": "cde7883b9050a1104f4ac19a1572aafd6e5d7323b68351aaf51fbf4beba54966",
        }],
        "note": "Arcticons by Donnnno and contributors. Iconify-normalized artwork is distributed under CC BY-SA 4.0.",
    },
    "garden-svg-icons": {
        "name": "Garden SVG Icons", "version": "1.2.8", "group": "UI",
        "upstream": "https://github.com/zendeskgarden/svg-icons",
        "license": "Apache-2.0", "license_class": "permissive", "license_file": "GARDEN-SVG-ICONS-LICENSE.txt",
        "sources": [iconify_source("@iconify-json/garden", "1.2.8", "c4d241c0b9f53fa83d862a7f701b3bbf04bce1955834ebbef0bb51b60976ddfb", 1491)],
        "license_sources": [{
            "file": "GARDEN-SVG-ICONS-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/zendeskgarden/svg-icons/22ae28f9ee05849feab0e1c690a98c60ef82817b/LICENSE.md",
            "sha256": "46ae5f0dc2e06a18cde8b06bdb45abea0b6e28d169e6eff2069536780304cf6e",
        }],
        "style_suffixes": [
            (f"-{style}-{size}", f"{style} {size}px")
            for style in ("fill", "stroke", "line") for size in (12, 16, 20, 26)
        ] + [(f"-{size}", f"{size}px") for size in (12, 16, 20, 26)],
        "note": "Zendesk Garden interface icons in multiple sizes and styles.",
    },
    "cryptocurrency-color": {
        "name": "Cryptocurrency Color Icons", "version": "1.2.4", "group": "Brands",
        "upstream": "https://github.com/atomiclabs/cryptocurrency-icons",
        "license": "CC0-1.0", "license_class": "restricted", "license_file": "CRYPTOCURRENCY-COLOR-LICENSE.txt",
        "sources": [iconify_source("@iconify-json/cryptocurrency-color", "1.2.4", "9458176ac1d49bf6d96aa21f0fdaf2ece2219255f15e33136523c88d71fbfb91", 483)],
        "license_sources": [{
            "file": "CRYPTOCURRENCY-COLOR-LICENSE.txt",
            "url": "https://raw.githubusercontent.com/atomiclabs/cryptocurrency-icons/1a63530be6e374711a8554f31b17e4cb92c25fa5/LICENSE.md",
            "sha256": "a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499",
        }],
        "note": "Cryptocurrency logos by Christopher Downer and contributors. The artwork is CC0. Individual logos may be subject to trademarks.",
    },
    "teenyicons": {
        "name": "Teenyicons", "version": "1.2.2", "group": "UI",
        "upstream": "https://www.npmjs.com/package/teenyicons",
        "license": "MIT", "license_class": "permissive", "license_file": "TEENYICONS-LICENSE.txt",
        "sources": [iconify_source("@iconify-json/teenyicons", "1.2.2", "d7433dcfad7bfe26ccab3482516050f8f2d9ea4aacf1d2cb0230694198adda2d", 1200)],
        "license_sources": [{
            "file": "TEENYICONS-LICENSE.txt",
            "url": "https://cdn.jsdelivr.net/npm/teenyicons@0.4.1/LICENSE",
            "sha256": "4c88ea0fa4b0cc7b6dbdadcddb3dfaa460329c08c84ac86842ebb3865f9379c1",
        }],
        "style_suffixes": [("-outline", "outline"), ("-solid", "solid")],
        "note": "15-pixel outline and solid interface icons by Anja van Staden.",
    },
}


if __name__ == "__main__":
    for library_id, config in LIBRARIES.items():
        build(library_id, config)
