# 언어별 아이콘 배포처와 비중복 후보

2026-11-22 기준. Icon Wiki의 58개 컬렉션과 Iconify의 280개 세트를 기준으로 대조했다. 중복의 단위는 **원작 아이콘 세트**다. 같은 제작자의 세트가 React·Java·Flutter로 각각 배포돼도 한 번만 센다. 서로 다른 세트 안에 비슷한 로고나 같은 도안이 있는지는 별도 문제다. [Icon Wiki 비교 기준](../data/collections.json) · [비교한 Iconify 목록](https://github.com/iconify/icon-sets/blob/d1fdcf54272b299075b4fbf21851147e8c3846f9/collections.md)

## 수록한 원본 세트 6개

| 원작 세트 | 발견한 배포처 | 확인한 원본 | 고유 항목 | 이용 조건과 집계 기준 |
|---|---|---|---:|---|
| Captain Icon | Java · Ikonli | [제작자 배포본](https://github.com/mariodelvalle/CaptainIcon/tree/81f037054e0da6aac2af3c3040db3706d5b1207c) | 375 | 원본 ZIP의 번호가 붙은 개별 SVG. Mario del Valle Guijarro의 CC BY-SA이며 제작자는 버전을 명시하지 않는다. [제작자 안내](https://mariodelvalle.github.io/CaptainIconWeb/) |
| Themify Icons | React Icons · Java Ikonli | [1.0.1 폰트와 CSS](https://github.com/lykmapipo/themify-icons/tree/9600186b24a7242f0e1e0a186983e6253301bb5d) | 352 | CSS에서 서로 다른 글리프에 연결한 이름 수. 폰트는 OFL-1.1, 코드는 MIT. [배포본 라이선스](https://github.com/lykmapipo/themify-icons#license) |
| Devicons · Theodore Vorillas | React Icons · Java Ikonli | [devicons 1.8.0](https://www.npmjs.com/package/devicons/v/1.8.0) | 192 | 배포본에 포함된 개별 SVG 수. MIT이며 브랜드 상표 조건이 있다. Icon Wiki에 수록된 devicons/devicon과 제작자·원본 저장소가 다르다. [Vorillas 원본](https://github.com/vorillaz/devicons) · [기존 Devicon](https://github.com/devicons/devicon) |
| Amazing Neo | Dart · IconForest | [제작자 2.0.0 배포 ZIP](https://amazingneo.com/storage/versions/amazing-neo-v2.0.0.zip) | 1,659 | 제작자 폰트 기준 일반 1,446개와 브랜드 213개. IconForest가 노출하는 Flutter 래퍼의 112개와 집계 범위가 다르다. 폰트는 OFL-1.1이며 브랜드에는 별도 상표 조건이 있다. [제작자 라이선스](https://amazingneo.com/license) |
| Microns | PHP · Blade Icons, Java · Ikonli, C# · MahApps | [microns 1.2.2](https://www.npmjs.com/package/microns/v/1.2.2) | 170 | 개별 SVG 172개 중 파일 내용이 같은 calendar/date, clock/time을 각각 한 번만 계산했다. SVG 아트워크는 CC BY-SA-4.0. [원본과 라이선스](https://github.com/stephenhutchings/microns) |
| Ikonate | PHP · Blade Icons | [ikonate 1.1.1](https://www.npmjs.com/package/ikonate/v/1.1.1) | 283 | icons 디렉터리의 SVG 수. MIT. 아이콘의 선 두께와 색은 사용하는 쪽에서 지정한다. [원본과 사용 예](https://github.com/eucalyptuss/ikonate) |
| **합계** | | | **3,031** | 위 여섯 배포본의 확인 범위 |

## 추가 조사한 16개 세트

11개 세트에서 3,660개 항목을 추가했다. 처음 확인한 6개 세트를 합하면 이번에 직접 수록한 항목은 17개 세트, 6,691개다.

| 수록한 세트 | 항목 수 | 범위 |
|---|---:|---|
| [Emblemicons](https://github.com/emblemicons/emblemicons.github.io) | 1,064 | 배경 없는 원본 SVG |
| [Govicons](https://github.com/540co/govicons) | 136 | 제작자 제공 SVG |
| [File Icon Vectors](https://github.com/dmhendricks/file-icon-vectors) | 23 | Classic의 일반 파일 확장자 도안. 별도 권리가 있는 브랜드 도안은 제외 |
| [Linecons](https://designmodo.com/linecons-free/) | 48 | 제작자 ZIP의 수정하지 않은 SVG |
| [OCI Icons](https://github.com/opencontainers/artwork) | 65 | OCI 인프라 아이콘 |
| [PaymentFont](https://github.com/AlexanderPoellmann/PaymentFont) | 116 | 폰트에서 추출한 결제 수단 글리프 |
| [525icons](https://github.com/runestro/525icons) | 310 | 브랜드 도안을 제외하고 확인한 일반 글리프 |
| [Linea](https://github.com/linea-io/Linea-Iconset) | 715 | 7개 카테고리의 기본 SVG |
| [PICOL](https://github.com/PicolSigns/Icons) | 549 | 제작자 배포 디렉터리의 SVG |
| [Keyrune](https://github.com/andrewgioia/keyrune) | 434 | Wizards of the Coast 카드 세트를 식별하는 원본 SVG |
| [Iconic Free](https://iconic.app/c/availability/free/) | 200 | 제작자가 무료로 분류한 200개와 대조한 SVG |

| 보류한 세트 | 제작자 조건 |
|---|---|
| Shopify Polaris Icons | 권리 행사는 Shopify 소프트웨어나 서비스와 연동하는 앱으로 한정된다. [패키지 라이선스](https://unpkg.com/@shopify/polaris-icons@9.3.1/LICENSE.md) |
| Iconsax | 개별 파일과 세트를 외부 플랫폼에서 배포하는 행위를 제한한다. [제작자 약관](https://docs.iconsax.io/license-and-terms/usage-manifesto) |
| Untitled UI Icons | 무료판에도 아이콘 재배포·재패키징 제한이 적용된다. [제작자 안내](https://www.untitledui.com/faqs) |
| Metrize Icons | 원본과 수정본 모두 세트 호스팅·재배포를 금지한다. [제작자 약관](https://oldsite.alessioatzeni.com/metrize-icons/) |
| Modern UI Icons | 전체 패키지를 배포하려면 제작자의 사전 허가가 필요하다. [배포본 라이선스](https://github.com/Templarian/WindowsIcons/blob/c869704c243966c6b2c29b893b6d2118e1702898/WindowsPhone/license.txt) |

## 중복·제한으로 제외한 후보

| 후보 | 판단 근거 |
|---|---|
| Grommet Icons, Circum Icons, IcoMoon Free, Elusive Icons | 앞서 언급한 여섯 후보 중 이 네 세트는 Iconify에 각각 grommet-icons, circum, icomoon-free, el로 등록돼 있다. [Iconify 세트 목록](https://github.com/iconify/icon-sets/blob/d1fdcf54272b299075b4fbf21851147e8c3846f9/collections.md) |
| Medicons, Win10, Blade Pixelicon, BPMN, Brandico | 배포 이름이 달라도 Iconify의 medical-icon, icons8, pixel, bpmn, brandico와 원작이 같다. [Blade Pixelicon의 원작 설명](https://github.com/daljo25/blade-pixelicon-icons) · [Iconify 세트 목록](https://github.com/iconify/icon-sets/blob/d1fdcf54272b299075b4fbf21851147e8c3846f9/collections.md) |
| Fork Awesome, RPG Awesome | 각각 Font Awesome과 Game-icons.net의 도안을 포함한다. 독자 추가분을 분리하기 전에는 전체를 신규 수량으로 세지 않는다. [Fork Awesome](https://github.com/ForkAwesome/Fork-Awesome) · [RPG Awesome의 출처](https://github.com/nagoshiashumari/Rpg-Awesome) |
| Hawcons | 두 기준 목록과는 겹치지 않지만, 제작자 Yannick Lung이 아이콘 자체의 판매·재배포를 금지한다. 배포 패키지의 요약 메타데이터와 동봉 약관이 다르다. [배포본에 동봉된 제작자 약관](https://unpkg.com/@icon/hawcons-stroke@1.0.0-alpha.3/LICENSE) |

## 언어별로 찾아볼 배포 목록

| 언어 | 목록 |
|---|---|
| JavaScript / TypeScript | [React Icons 세트·버전·원작 표](https://github.com/react-icons/react-icons#icons) |
| PHP | [Blade Icons 패키지 목록](https://github.com/driesvints/blade-icons) · [검색 사이트가 설치하는 패키지](https://github.com/blade-ui-kit/blade-ui-kit.com/blob/main/composer.json) |
| Python | [QtAwesome 수록 폰트](https://pypi.org/project/QtAwesome/) · [pyconify는 Iconify API 클라이언트](https://pypi.org/project/pyconify/) |
| Java | [Ikonli 팩별 원작과 Maven 모듈](https://kordamp.org/ikonli/) |
| Kotlin | [Compose Icons 팩별 의존성과 목록](https://github.com/DevSrSouza/compose-icons) |
| Swift | [SwiftUIFontIcon 지원 폰트](https://github.com/huybuidac/SwiftUIFontIcon#supported-fonts) |
| Dart | [IconForest의 Flutter 패키지 목록](https://github.com/iconforest/icon_forest) |
| C# | [MahApps.Metro.IconPacks 수록 팩](https://github.com/MahApps/MahApps.Metro.IconPacks) |
| Rust | [icondata의 개별 crate와 SVG 데이터](https://docs.rs/icondata/latest/icondata/) |
| Go | [assaidy/icons의 원작·라이선스 표](https://pkg.go.dev/github.com/assaidy/icons) |
| Ruby | [Icons 코어 gem](https://github.com/Rails-Designer/icons) · [Rails Icons](https://github.com/Rails-Designer/rails_icons) |
