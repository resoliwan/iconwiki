# 언어별 아이콘 배포처와 비중복 후보

첫 조사에서는 Icon Wiki 58개 컬렉션과 Iconify 280개 세트를 대조했다. 후속 조사는 아래의 75개 컬렉션을 기준으로 했다. 중복의 단위는 **원작 아이콘 세트**다. 같은 제작자의 세트가 React·Java·Flutter로 각각 배포돼도 한 번만 센다. 서로 다른 세트 안에 비슷한 로고나 같은 도안이 있는지는 별도 문제다. [Icon Wiki 비교 기준](../data/collections.json) · [비교한 Iconify 목록](https://github.com/iconify/icon-sets/blob/d1fdcf54272b299075b4fbf21851147e8c3846f9/collections.md)

## 수록 결과

아래에서 조사한 8개 세트와 후속 후보 18개를 합쳐 **26개 세트, 10,877개 검색 항목**을 추가했다. 앞의 8개 세트는 6,719개, 후속 18개 세트는 4,158개다. 원본 파일이 같은 세트 내 별칭은 검색어로 합쳤고, 기존 Devicon의 PowerShell과 파일 내용이 같은 SVGL 항목은 제외했다. Bioicons는 목록에 기록된 수치보다 고정한 저장소에 실제 SVG가 더 많아 파일을 기준으로 집계했다. 컬렉션마다 같은 브랜드나 대상을 그린 다른 도안이 포함될 수 있다. [세트별 실수록 수](../README.md#included-libraries) · [원본 버전과 선별 기준](../data/sources/feed-packs.json)

## 바로 가져올 수 있는 아이콘 목록

2026-11-22 확인. 아래는 Iconify 밖에서 원작 저장소를 발견하거나 아이콘 이름·파일 위치를 읽을 수 있는 배포처다. 기존 조사 문서, Icon Wiki 75개 컬렉션, Iconify 280개 세트와 대조한 예시 8개의 목록 URL과 에셋 경로는 [CSV](./icon-source-feeds.csv)에 담았다. 신규 여부는 세트 단위로 확인했고 개별 SVG 중복과 재배포 조건은 별도 검토가 필요하다.

| 원하는 데이터 | 읽을 파일 | 확인한 내용 |
|---|---|---|
| 일반 아이콘 세트의 원작 저장소 목록 | [IconSearch YAML 원문](https://raw.githubusercontent.com/VectorLogoZone/git-svg-icons/main/data/iconsearch.yaml) | 166개 항목. 각 행의 repo, branch, directory로 실제 SVG 폴더를 찾을 수 있다. Adobe Spectrum Workflow Icons와 Pictogramas의 지정 경로에서 각각 SVG 396개와 53개를 확인했다. |
| 브랜드·로고 세트의 원작 저장소 목록 | [LogoSearch YAML 원문](https://raw.githubusercontent.com/VectorLogoZone/git-svg-icons/main/data/logosearch.yaml) | 123개 항목. 예를 들어 SVGL은 [로고 메타데이터](https://github.com/pheralb/svgl/blob/main/src/data/svgs.ts)와 [SVG 디렉터리](https://github.com/pheralb/svgl/tree/main/static/library)를 제공한다. 두 YAML의 항목에는 같은 저장소의 다른 경로와 이미 수록한 세트도 포함된다. |
| 여러 팩에 공통 형식으로 정리된 아이콘 이름과 SVG | [Standard Icons 모듈 목록 JSON](https://api.github.com/repos/thecreation/standard-icons/contents/modules) | 모듈 디렉터리 70개. 팩별 manifest.json의 icons와 같은 모듈의 icons/ 디렉터리를 함께 쓴다. 명단에서 Dripicons 200개, Caomei Icons 376개, Gonzocons 100개, IcoFont 2,095개를 확인했다. [Dripicons 목록 예시](https://raw.githubusercontent.com/thecreation/standard-icons/master/modules/dripicons/manifest.json) |
| 과학·의학 일러스트의 개별 아이콘 목록 | [Bioicons 목록 JSON](https://raw.githubusercontent.com/duerrsimon/bioicons/main/static/icons/icons.json) | 2,804개 레코드. 각 행에 이름·카테고리·라이선스·작가가 있고 [같은 저장소](https://github.com/duerrsimon/bioicons/tree/main/static/icons)에서 SVG를 제공한다. |

## 후속 조사 · 다른 아이콘 모음에서 찾은 후보 18개

2026-11-22에 Icon Wiki의 현재 75개 컬렉션, Iconify의 280개 세트, 앞선 조사에서 보류하거나 제외한 목록까지 다시 대조했다. 아래 18개는 이들 목록에 별도 세트로 올라 있지 않은 후보들이다. 숫자는 표에 적은 배포본의 글리프나 파일 수다. 로고와 국기는 여러 세트에서 같은 대상을 그리므로 개별 도안의 중복 수와 재배포 조건은 별도 확인이 필요하다. [Icon Wiki 비교 시점](https://github.com/resoliwan/iconwiki/blob/bc6d4f41e3183705d3c7ace5c0fc33a77c9c1af9/data/collections.json) · [Iconify 비교 시점](https://github.com/iconify/icon-sets/blob/d1fdcf54272b299075b4fbf21851147e8c3846f9/collections.md)

| 모음 | 형태 | 이번에 찾은 새 후보 |
|---|---|---:|
| [Fontello](https://github.com/fontello/fontello/tree/71330f51d11b00fa75b6c516db2ea4d62da67330/src) | 여러 제작자의 아이콘 폰트에서 글리프를 골라 하나의 폰트로 내보내는 도구 | 3 |
| [Nerd Fonts](https://github.com/ryanoasis/nerd-fonts/blob/adbd16ab7ca911eaca7ce3b0f2b7994207c7ecae/src/glyphs/README.md) | 파일 종류·터미널 상태·전원 기호 등을 개발자용 폰트에 묶어 배포 | 6 |
| [svg-icon](https://github.com/leungwensen/svg-icon/tree/8b84d725b0d2be8f5d87cac7f2c386682ce43563#svg-icon-collections) | 원작별 SVG 스프라이트를 실제로 배포하는 npm 패키지 | 2 |
| [Awesome Icons](https://github.com/notlmn/awesome-icons/blob/ada49832602b1109aa2441598d3740a44d80e001/readme.md) | 로고·지도·국기·CSS 아이콘의 제작자 저장소를 연결하는 디렉터리 | 7 |

### 폰트와 SVG 묶음에서 확인한 11개

| 원작 세트 | 모음 | 배포본에서 확인한 규모 또는 용도 |
|---|---|---|
| [MFG Labs Iconset](https://github.com/fontello/mfglabs.font/blob/5d5fb76bb9584584512b6113a40b748ff1ccf9eb/config.yml) | Fontello, svg-icon | Fontello 글리프 **153개**. 같은 원작이 두 모음에 있어 한 세트로 계산 |
| [Modern Pictograms](https://github.com/fontello/modernpics.font/blob/78eafe8692c8f340b20533b43318945d0f78214a/config.yml) | Fontello | John Caserta의 픽토그램 **91개** |
| [Zocial](https://github.com/fontello/zocial.font/blob/22f90e263e0d5295c339846d1ff222028f438a2b/config.yml) | Fontello, svg-icon | Fontello에서 소셜 서비스용 글리프 **103개** |
| [Geomicons Open](https://github.com/jxnblk/geomicons-open) | svg-icon | 32px 그리드 UI 아이콘. 배포 스프라이트에 **56개**. [스프라이트](https://github.com/leungwensen/svg-icon/blob/8b84d725b0d2be8f5d87cac7f2c386682ce43563/dist/sprite/symbol/geom.svg) |
| [Payment Webfont](https://github.com/orlandotm/payment-webfont) | svg-icon | Orlando의 결제 수단 아이콘 **34개**. 현재 수록된 PaymentFont와는 제작자가 다르며, 그려진 결제 브랜드는 겹칠 수 있다. [스프라이트](https://github.com/leungwensen/svg-icon/blob/8b84d725b0d2be8f5d87cac7f2c386682ce43563/dist/sprite/symbol/payment-web.svg) |
| [Seti UI](https://github.com/jesseweed/seti-ui) | Nerd Fonts | VS Code 기본 파일 아이콘의 원작. Nerd Fonts의 seti 이름 167개가 서로 다른 코드 포인트 160개에 대응 |
| [Powerline Symbols](https://github.com/powerline/powerline) | Nerd Fonts | 터미널 상태줄의 구분자와 기호. pl 코드 포인트 7개 |
| [Powerline Extra Symbols](https://github.com/ryanoasis/powerline-extra-symbols) | Nerd Fonts | Powerline용 추가 구분자. ple 코드 포인트 33개 |
| [Pomicons](https://github.com/gabrielelana/pomicons) | Nerd Fonts | 포모도로 작업·휴식 상태 기호. Nerd Fonts의 pom 코드 포인트 11개 |
| [IEC Power Symbols](https://github.com/jloughry/Unicode) | Nerd Fonts | 전원·대기·절전 기호. iec 코드 포인트 5개 |
| [Font Awesome Extension](https://github.com/AndreLZGava/font-awesome-extension) | Nerd Fonts | 독립 확장 프로젝트. fae 코드 포인트 170개. 기존 Font Awesome과 도안 단위 비교 필요 |

Nerd Fonts 수량은 접두사별로 이름 별칭을 합친 코드 포인트 수다. [집계한 Nerd Fonts 이름표](https://github.com/ryanoasis/nerd-fonts/blob/adbd16ab7ca911eaca7ce3b0f2b7994207c7ecae/glyphnames.json)

### 디렉터리에서 원본을 확인한 7개

| 원작 세트 | 내용 |
|---|---|
| [Super Tiny Icons](https://github.com/edent/SuperTinyIcons/tree/d532b8a9e8a96ed5462f3813106f0b1e230249dc/images/svg) | 1KB 이하로 만든 로고 SVG **479개**. 원본 크기별 PNG와 참고 이미지는 제외 |
| [FlagKit](https://github.com/madebybowtie/FlagKit/tree/e7c542fc43dcfe1bf9bcdaa4898ad8d119a84407/Assets/SVG) | 국기·지역기 SVG **255개**. Iconify의 Yummygum/Flagpack과 별개의 프로젝트 |
| [Mapsicon](https://github.com/djaiss/mapsicon) | 국가의 지리적 윤곽을 표현한 실루엣. SVG와 여러 해상도의 PNG 제공 |
| [Browser Logos](https://github.com/alrra/browser-logos) | 브라우저 로고의 현재·과거 디자인을 수집. 각 브랜드 권리 확인 필요 |
| [Vector Logo Zone](https://github.com/VectorLogoZone/vectorlogozone) | 일정한 크기와 레이아웃으로 정리한 브랜드 SVG. 원작 브랜드·기존 로고 세트와의 대조 필요 |
| [CSS ICON](https://github.com/wentin/cssicon) | Wenting Zhang의 CSS 도형 아이콘. CSS로 그린 원본 |
| [icono](https://github.com/saeedalipoor/icono) | CSS 클래스만으로 렌더링하는 Saeed Alipoor의 아이콘 세트 |

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
