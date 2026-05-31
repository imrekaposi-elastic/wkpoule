"""Seed the database with World Cup 2026 teams, venues, matches, and fun comments."""

import random
import sys
from datetime import datetime, timezone

from app.config import get_settings
from app.database import Base, engine, SessionLocal
from app.models.user import User
from app.models.team import Team
from app.models.team_player import TeamPlayer
from app.models.venue import Venue
from app.models.match import Match
from app.models.prediction import Prediction
from app.models.fun_comment import FunComment
from app.auth import hash_password
from app.data.team_profiles import build_team_profile
from app.data.team_squads import build_team_squad

# ---------------------------------------------------------------------------
# Venues (16 stadiums across USA, Canada, Mexico)
# ---------------------------------------------------------------------------
VENUES = [
    {
        "name": "Estadio Azteca", "city": "Mexico City", "country": "Mexico",
        "capacity": 87523, "latitude": 19.3029, "longitude": -99.1505,
        "year_built": 1966,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Estadio_Azteca_desde_el_aire_1.jpg?width=800",
        "rating": 4, "expected_temp_celsius": 20.0, "city_attractiveness": 4,
        "review_en": "One of the most iconic stadiums in world football history. Hosted two World Cup finals (1970, 1986) and witnessed Maradona's 'Hand of God.' The atmosphere is electric but the aging infrastructure shows its years.",
        "review_nl": "Een van de meest iconische stadions in de voetbalgeschiedenis. Gastheer van twee WK-finales (1970, 1986) en getuige van Maradona's 'Hand van God.' De sfeer is elektrisch, maar de verouderde infrastructuur laat zijn leeftijd zien.",
        "review_pt": "Um dos estádios mais icônicos da história do futebol mundial. Sediou duas finais de Copa do Mundo (1970, 1986) e testemunhou a 'Mão de Deus' de Maradona. A atmosfera é elétrica, mas a infraestrutura envelhecida mostra seus anos.",
        "review_de": "Eines der ikonischsten Stadien der Fußballgeschichte. Austragungsort zweier WM-Finals (1970, 1986) und Schauplatz von Maradonas 'Hand Gottes.' Die Atmosphäre ist elektrisierend, aber die alternde Infrastruktur zeigt ihr Alter.",
        "review_he": "אחד האצטדיונים האייקוניים ביותר בהיסטוריית הכדורגל העולמי. אירח שני גמרי מונדיאל (1970, 1986) ואת רגע ״יד האלוהים״ של מראדונה. האווירה חשמלית, אך חלק מהתשתית מראה את גיל האצטדיון.",
        "accessibility_en": "Well connected by Mexico City Metro (Line 2, Tasqueña direction). The Azteca station is right next to the stadium. Heavy traffic on match days — arrive early or use public transport.",
        "accessibility_nl": "Goed bereikbaar met de metro van Mexico-Stad (lijn 2, richting Tasqueña). Het station Azteca ligt direct naast het stadion. Druk verkeer op wedstrijddagen — kom vroeg of gebruik het openbaar vervoer.",
        "accessibility_pt": "Bem conectado pelo metrô da Cidade do México (Linha 2, direção Tasqueña). A estação Azteca fica ao lado do estádio. Trânsito pesado em dias de jogo — chegue cedo ou use transporte público.",
        "accessibility_de": "Gut angebunden durch die Metro von Mexiko-Stadt (Linie 2, Richtung Tasqueña). Die Station Azteca liegt direkt neben dem Stadion. Starker Verkehr an Spieltagen — früh anreisen oder öffentliche Verkehrsmittel nutzen.",
        "accessibility_he": "מחובר היטב לרכבת התחתית של מקסיקו סיטי (קו 2, לכיוון טסקניה). תחנת אצטקה צמודה לאצטדיון. בימי משחק התנועה כבדה — מומלץ להגיע מוקדם או להשתמש בתחבורה ציבורית.",
    },
    {
        "name": "Estadio Akron", "city": "Zapopan", "country": "Mexico",
        "capacity": 49850, "latitude": 20.6822, "longitude": -103.4625,
        "year_built": 2010,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Akron_Stadium_(Chivas).jpg?width=800",
        "rating": 4, "expected_temp_celsius": 27.0, "city_attractiveness": 3,
        "review_en": "A stunning modern stadium with a unique volcanic rock-inspired design. Home to Chivas de Guadalajara, it offers excellent sightlines and a passionate atmosphere. A jewel of Mexican football architecture.",
        "review_nl": "Een prachtig modern stadion met een uniek ontwerp geïnspireerd op vulkanisch gesteente. Thuisbasis van Chivas de Guadalajara, het biedt uitstekende zichtlijnen en een gepassioneerde sfeer. Een juweeltje van de Mexicaanse voetbalarchitectuur.",
        "review_pt": "Um estádio moderno deslumbrante com um design único inspirado em rochas vulcânicas. Casa do Chivas de Guadalajara, oferece excelentes linhas de visão e uma atmosfera apaixonada. Uma joia da arquitetura do futebol mexicano.",
        "review_de": "Ein atemberaubendes modernes Stadion mit einem einzigartigen, von Vulkangestein inspirierten Design. Heimat von Chivas de Guadalajara, bietet es hervorragende Sichtlinien und eine leidenschaftliche Atmosphäre. Ein Juwel der mexikanischen Fußballarchitektur.",
        "review_he": "אצטדיון מודרני ומרשים בעיצוב ייחודי בהשראת סלעים געשיים. ביתה של צ׳יבאס גוודלחרה — ראות מצוינת למגרש ואווירה נלהבת. פנינה באדריכלות הכדורגל המקסיקנית.",
        "accessibility_en": "Located in the suburbs of Guadalajara. Accessible by car or taxi; limited public transit. Shuttle services are typically available on match days from central Guadalajara.",
        "accessibility_nl": "Gelegen in de buitenwijken van Guadalajara. Bereikbaar per auto of taxi; beperkt openbaar vervoer. Pendeldiensten zijn doorgaans beschikbaar op wedstrijddagen vanuit het centrum van Guadalajara.",
        "accessibility_pt": "Localizado nos subúrbios de Guadalajara. Acessível de carro ou táxi; transporte público limitado. Serviços de shuttle geralmente disponíveis em dias de jogo a partir do centro de Guadalajara.",
        "accessibility_de": "In den Vororten von Guadalajara gelegen. Erreichbar mit Auto oder Taxi; begrenzter öffentlicher Nahverkehr. An Spieltagen gibt es in der Regel Shuttlebusse vom Zentrum Guadalajaras.",
        "accessibility_he": "בפרברי גוודלחרה. נגיש ברכב או במונית; תחבורה ציבורית מוגבלת. בימי משחק לרוב פועלות הסעות מהמרכז.",
    },
    {
        "name": "Estadio BBVA", "city": "Guadalupe", "country": "Mexico",
        "capacity": 53500, "latitude": 25.6690, "longitude": -100.2446,
        "year_built": 2015,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Estadio_BBVA_Bancomer_(1).jpg?width=800",
        "rating": 5, "expected_temp_celsius": 33.0, "city_attractiveness": 3,
        "review_en": "A world-class stadium that won the World Stadium Award in 2020. Its dramatic sloping roof and open design provide spectacular mountain views. The heat in Monterrey can be brutal during summer, but the venue itself is top-notch.",
        "review_nl": "Een stadion van wereldklasse dat in 2020 de World Stadium Award won. Het spectaculaire hellende dak en open ontwerp bieden adembenemend uitzicht op de bergen. De hitte in Monterrey kan meedogenloos zijn in de zomer, maar het stadion zelf is van topkwaliteit.",
        "review_pt": "Um estádio de classe mundial que ganhou o World Stadium Award em 2020. Seu telhado inclinado dramático e design aberto proporcionam vistas espetaculares das montanhas. O calor em Monterrey pode ser brutal no verão, mas o estádio em si é excelente.",
        "review_de": "Ein Weltklasse-Stadion, das 2020 den World Stadium Award gewann. Das dramatisch geneigte Dach und das offene Design bieten spektakuläre Bergblicke. Die Hitze in Monterrey kann im Sommer brutal sein, aber das Stadion selbst ist erstklassig.",
        "review_he": "אצטדיון ברמה עולמית שזכה בפרס World Stadium Award ב־2020. הגג המשופע והעיצוב הפתוח מציעים נוף הרים מרהיב. הקיץ במונטריי קשה, אך האצטדיון עצמו מהשורה הראשונה.",
        "accessibility_en": "Located in the Monterrey metropolitan area. Reachable by Metrorrey (light rail) and bus. Taxi and ride-sharing apps work well. The city is compact and navigable.",
        "accessibility_nl": "Gelegen in het grootstedelijk gebied van Monterrey. Bereikbaar met Metrorrey (lightrail) en bus. Taxi en ride-sharing apps werken goed. De stad is compact en overzichtelijk.",
        "accessibility_pt": "Localizado na área metropolitana de Monterrey. Acessível pelo Metrorrey (metrô leve) e ônibus. Táxi e aplicativos de transporte funcionam bem. A cidade é compacta e fácil de navegar.",
        "accessibility_de": "Im Großraum Monterrey gelegen. Erreichbar mit Metrorrey (Stadtbahn) und Bus. Taxi und Ride-Sharing-Apps funktionieren gut. Die Stadt ist kompakt und überschaubar.",
        "accessibility_he": "במטרופולין מונטרייה. נגיש ב־Metrorrey (רכבת קלה) ובאוטובוס. מוניות ואפליקציות הסעה נוחות. העיר קומפקטית וקלה לניווט.",
    },
    {
        "name": "BMO Field", "city": "Toronto", "country": "Canada",
        "capacity": 30000, "latitude": 43.6335, "longitude": -79.4186,
        "year_built": 2007,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Toronto_-_ON_-_BMO_Field.jpg?width=800",
        "rating": 3, "expected_temp_celsius": 22.0, "city_attractiveness": 5,
        "review_en": "The smallest venue in the tournament but with an intimate, passionate atmosphere. Located on Toronto's waterfront near Exhibition Place. Being expanded for the World Cup, but still the coziest ground — great for atmosphere, less so for capacity.",
        "review_nl": "Het kleinste stadion van het toernooi, maar met een intieme, gepassioneerde sfeer. Gelegen aan de waterkant van Toronto bij Exhibition Place. Wordt uitgebreid voor het WK, maar blijft het gezelligste stadion — geweldig voor de sfeer, minder voor de capaciteit.",
        "review_pt": "O menor estádio do torneio, mas com uma atmosfera íntima e apaixonada. Localizado na orla de Toronto, perto do Exhibition Place. Sendo ampliado para a Copa do Mundo, mas ainda o mais aconchegante — ótimo para atmosfera, menos para capacidade.",
        "review_de": "Das kleinste Stadion des Turniers, aber mit einer intimen, leidenschaftlichen Atmosphäre. Am Ufer Torontos in der Nähe von Exhibition Place gelegen. Wird für die WM erweitert, bleibt aber das gemütlichste — großartig für Atmosphäre, weniger für Kapazität.",
        "review_he": "האצטדיון הקטן ביותר בטורניר, אך עם אווירה אינטימית וסוערת. על חוף טורונטו ליד אקסיבישן פלייס. מורחב למונדיאל ועדיין האצטדיון הכי ״ביתי״ — מצוין לקהל, פחות למספר מושבים.",
        "accessibility_en": "Excellent location on Toronto's waterfront. Accessible by TTC streetcar (509, 511) and walking from Union Station. The city has world-class public transit, restaurants, and hotels nearby.",
        "accessibility_nl": "Uitstekende locatie aan de waterkant van Toronto. Bereikbaar met TTC-tram (509, 511) en te voet vanaf Union Station. De stad heeft uitstekend openbaar vervoer, restaurants en hotels in de buurt.",
        "accessibility_pt": "Excelente localização na orla de Toronto. Acessível por bonde TTC (509, 511) e a pé a partir da Union Station. A cidade tem transporte público de classe mundial, restaurantes e hotéis próximos.",
        "accessibility_de": "Ausgezeichnete Lage am Ufer Torontos. Erreichbar mit TTC-Straßenbahn (509, 511) und zu Fuß vom Union Station. Die Stadt hat erstklassigen öffentlichen Nahverkehr, Restaurants und Hotels in der Nähe.",
        "accessibility_he": "מיקום מצוין על חוף טורונטו. נגיש בחשמולית TTC (509, 511) וברגל מתחנת יוניון. תחבורה ציבורית, מסעדות ומלונות ברמה גבוהה בקרבת מקום.",
    },
    {
        "name": "BC Place", "city": "Vancouver", "country": "Canada",
        "capacity": 54500, "latitude": 49.2768, "longitude": -123.1120,
        "year_built": 1983,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/BCplace_stadium.jpg?width=800",
        "rating": 4, "expected_temp_celsius": 18.0, "city_attractiveness": 5,
        "review_en": "A retractable-roof stadium in the heart of Vancouver with stunning mountain and harbor views from the surrounding area. Renovated in 2011 with a modern roof. The mild Vancouver climate is a bonus for summer football.",
        "review_nl": "Een stadion met uitschuifbaar dak in het hart van Vancouver met prachtig uitzicht op de bergen en de haven vanuit de omgeving. Gerenoveerd in 2011 met een modern dak. Het milde Vancouver-klimaat is een bonus voor zomervoetbal.",
        "review_pt": "Um estádio com teto retrátil no coração de Vancouver, com vistas deslumbrantes das montanhas e do porto na área circundante. Renovado em 2011 com um teto moderno. O clima ameno de Vancouver é um bônus para o futebol de verão.",
        "review_de": "Ein Stadion mit einziehbarem Dach im Herzen Vancouvers mit atemberaubenden Berg- und Hafenblicken aus der Umgebung. 2011 mit einem modernen Dach renoviert. Das milde Klima Vancouvers ist ein Bonus für Sommerfußball.",
        "review_he": "אצטדיון עם גג נשלף במרכז ונקובר, עם נוף הרים ונמל מרהיב מהסביבה. שופץ ב־2011 עם גג מודרני. האקלים הנוח של ונקובר מיטיב עם כדורגל קיץ.",
        "accessibility_en": "Downtown location with SkyTrain (Stadium-Chinatown station) right at the door. Walkable from most downtown hotels. Vancouver is very easy to navigate by transit, bike, or on foot.",
        "accessibility_nl": "Locatie in het centrum met SkyTrain (station Stadium-Chinatown) direct voor de deur. Op loopafstand van de meeste hotels in het centrum. Vancouver is zeer gemakkelijk te bereiken per openbaar vervoer, fiets of te voet.",
        "accessibility_pt": "Localização no centro com SkyTrain (estação Stadium-Chinatown) bem na porta. Caminhável a partir da maioria dos hotéis do centro. Vancouver é muito fácil de navegar por transporte público, bicicleta ou a pé.",
        "accessibility_de": "Innenstadtlage mit SkyTrain (Station Stadium-Chinatown) direkt vor der Tür. Zu Fuß von den meisten Innenstadt-Hotels erreichbar. Vancouver ist sehr einfach per ÖPNV, Fahrrad oder zu Fuß zu erkunden.",
        "accessibility_he": "במרכז העיר — רכבת SkyTrain (תחנת סטדיום־צ׳יינהטאון) ליד הכניסה. במרחק הליכה מרוב מלונות המרכז. ונקובר נוחה מאוד לתחבורה ציבורית, אופניים או רגלית.",
    },
    {
        "name": "MetLife Stadium", "city": "East Rutherford", "country": "USA",
        "capacity": 82500, "latitude": 40.8128, "longitude": -74.0742,
        "year_built": 2010,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Metlife_stadium_(Aerial_view).jpg?width=800",
        "rating": 4, "expected_temp_celsius": 27.0, "city_attractiveness": 5,
        "review_en": "The venue for the 2026 World Cup Final. A massive, modern stadium that hosts two NFL teams. While it lacks a roof and architectural flair, its sheer scale and proximity to New York City make it a premier venue. The atmosphere for big events is outstanding.",
        "review_nl": "Het stadion voor de WK-finale van 2026. Een enorm, modern stadion dat twee NFL-teams huisvest. Hoewel het een dak en architecturale flair mist, maken de schaal en nabijheid van New York City het tot een toplocatie. De sfeer bij grote evenementen is uitstekend.",
        "review_pt": "O estádio da final da Copa do Mundo de 2026. Um estádio massivo e moderno que abriga duas equipes da NFL. Embora falte teto e estilo arquitetônico, sua escala e proximidade com Nova York o tornam um local de primeira. A atmosfera para grandes eventos é excelente.",
        "review_de": "Der Austragungsort des WM-Finals 2026. Ein riesiges, modernes Stadion, das zwei NFL-Teams beherbergt. Obwohl es an einem Dach und architektonischem Flair fehlt, machen seine schiere Größe und die Nähe zu New York City es zu einer erstklassigen Spielstätte.",
        "review_he": "אצטדיון גמר המונדיאל 2026. מתחם ענק ומודרני שמארח שתי קבוצות NFL. אין גג ופחות ״פלא אדריכלי״, אך הממדים והקרבה לניו יורק הופכים אותו לאחד האתרים הבולטים. אווירה מצוינת באירועים גדולים.",
        "accessibility_en": "Located in New Jersey, ~10km from Manhattan. NJ Transit trains and buses serve the Meadowlands complex. Shuttles from NYC on match days. Driving is possible but parking is expensive and traffic heavy.",
        "accessibility_nl": "Gelegen in New Jersey, ~10 km van Manhattan. NJ Transit-treinen en bussen bedienen het Meadowlands-complex. Pendeldiensten vanuit NYC op wedstrijddagen. Autorijden is mogelijk, maar parkeren is duur en het verkeer is druk.",
        "accessibility_pt": "Localizado em Nova Jersey, ~10 km de Manhattan. Trens e ônibus NJ Transit atendem o complexo Meadowlands. Shuttles de NYC em dias de jogo. Dirigir é possível, mas estacionamento é caro e o trânsito pesado.",
        "accessibility_de": "In New Jersey gelegen, ~10 km von Manhattan. NJ Transit-Züge und Busse bedienen den Meadowlands-Komplex. Shuttles aus NYC an Spieltagen. Autofahren ist möglich, aber Parken ist teuer und der Verkehr stark.",
        "accessibility_he": "בניו ג׳רזי, כ־10 ק״מ ממנהטן. רכבות ואוטובוסים של NJ Transit למתחם מדולנדס. הסעות מניו יורק בימי משחק. ניתן להגיע ברכב אך החניה יקרה והעומס גבוה.",
    },
    {
        "name": "Gillette Stadium", "city": "Foxborough", "country": "USA",
        "capacity": 65878, "latitude": 42.0909, "longitude": -71.2643,
        "year_built": 2002,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Gillette_Stadium_Outdoor.jpg?width=800",
        "rating": 3, "expected_temp_celsius": 25.0, "city_attractiveness": 3,
        "review_en": "Home of the New England Patriots (NFL) and Revolution (MLS). A solid but unspectacular venue in a suburban setting. The stadium itself is functional and comfortable, but Foxborough's remote location makes it less convenient than urban venues.",
        "review_nl": "Thuisbasis van de New England Patriots (NFL) en Revolution (MLS). Een degelijk maar onopvallend stadion in een voorstedelijke omgeving. Het stadion zelf is functioneel en comfortabel, maar de afgelegen locatie van Foxborough maakt het minder handig dan stadsstadions.",
        "review_pt": "Casa dos New England Patriots (NFL) e Revolution (MLS). Um estádio sólido mas sem grande destaque em um ambiente suburbano. O estádio em si é funcional e confortável, mas a localização remota de Foxborough o torna menos conveniente que estádios urbanos.",
        "review_de": "Heimat der New England Patriots (NFL) und Revolution (MLS). Ein solides, aber unspektakuläres Stadion in vorstädtischer Lage. Das Stadion selbst ist funktional und komfortabel, aber Foxboroughs abgelegene Lage macht es weniger praktisch als urbane Spielstätten.",
        "review_he": "ביתם של ניו אינגלנד פטריוטס (NFL) ורבולושן (MLS). אצטדיון יציב אך פחות דרמטי בפרברים. המבנה פונקציונלי ונוח, אך המיקום המרוחק של פוקסבורו פחות נוח מאצטדיוני עיר.",
        "accessibility_en": "About 45 minutes southwest of Boston with limited public transit. Commuter rail runs from South Station on match days. Most fans drive — ample parking but heavy traffic. Plan extra travel time.",
        "accessibility_nl": "Ongeveer 45 minuten ten zuidwesten van Boston met beperkt openbaar vervoer. Forensentrein rijdt vanaf South Station op wedstrijddagen. De meeste fans rijden — ruime parkeerplaatsen maar druk verkeer. Plan extra reistijd in.",
        "accessibility_pt": "Cerca de 45 minutos a sudoeste de Boston com transporte público limitado. Trem suburbano opera a partir de South Station em dias de jogo. A maioria dos torcedores dirige — amplo estacionamento mas trânsito pesado. Planeje tempo extra de viagem.",
        "accessibility_de": "Etwa 45 Minuten südwestlich von Boston mit begrenztem öffentlichem Nahverkehr. Pendlerzüge fahren an Spieltagen von South Station. Die meisten Fans fahren mit dem Auto — ausreichend Parkplätze, aber starker Verkehr. Planen Sie zusätzliche Reisezeit ein.",
        "accessibility_he": "כ־45 דקות דרומית־מערבית לבוסטון; תחבורה ציבורית מוגבלת. רכבת פרברים מסאות׳ סטיישן בימי משחק. רוב האוהדים מגיעים ברכב — חניה בשפע אך פקקים. כדאי לתכנן זמן נסיעה נוסף.",
    },
    {
        "name": "Lincoln Financial Field", "city": "Philadelphia", "country": "USA",
        "capacity": 69796, "latitude": 39.9008, "longitude": -75.1675,
        "year_built": 2003,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Lincoln_Financial_Field,_Philadelphia.jpg?width=800",
        "rating": 4, "expected_temp_celsius": 28.0, "city_attractiveness": 4,
        "review_en": "Home of the Philadelphia Eagles (NFL). Known for its passionate, intense fans. The stadium is modern and well-maintained with great sightlines. Philadelphia's sports culture guarantees an electric atmosphere for every match.",
        "review_nl": "Thuisbasis van de Philadelphia Eagles (NFL). Bekend om zijn gepassioneerde, intense fans. Het stadion is modern en goed onderhouden met uitstekende zichtlijnen. De sportcultuur van Philadelphia garandeert een elektrische sfeer bij elke wedstrijd.",
        "review_pt": "Casa dos Philadelphia Eagles (NFL). Conhecido por seus torcedores apaixonados e intensos. O estádio é moderno e bem mantido com ótimas linhas de visão. A cultura esportiva da Filadélfia garante uma atmosfera elétrica em cada jogo.",
        "review_de": "Heimat der Philadelphia Eagles (NFL). Bekannt für seine leidenschaftlichen, intensiven Fans. Das Stadion ist modern und gepflegt mit großartigen Sichtlinien. Philadelphias Sportkultur garantiert eine elektrisierende Atmosphäre bei jedem Spiel.",
        "review_he": "ביתה של פילדלפיה איגלס (NFL). ידועה באוהדים סוערים ונלהבים. האצטדיון מודרן ומטופח עם ראות מצוינת. תרבות הספורט של פילדלפיה מבטיחה אווירה חשמלית בכל משחק.",
        "accessibility_en": "Located in South Philadelphia's sports complex. SEPTA subway (Broad Street Line) stops at NRG station. Easy access from downtown and 30th Street Station (Amtrak). Very walkable sports district.",
        "accessibility_nl": "Gelegen in het sportcomplex van Zuid-Philadelphia. SEPTA-metro (Broad Street Line) stopt bij NRG-station. Gemakkelijke toegang vanuit het centrum en 30th Street Station (Amtrak). Zeer goed te voet bereikbaar sportdistrict.",
        "accessibility_pt": "Localizado no complexo esportivo do sul da Filadélfia. Metrô SEPTA (Broad Street Line) para na estação NRG. Fácil acesso do centro e da 30th Street Station (Amtrak). Distrito esportivo muito acessível a pé.",
        "accessibility_de": "Im Sportkomplex von Süd-Philadelphia gelegen. SEPTA-U-Bahn (Broad Street Line) hält an der NRG-Station. Leichter Zugang aus der Innenstadt und vom 30th Street Station (Amtrak). Sehr fußgängerfreundliches Sportviertel.",
        "accessibility_he": "במתחם הספורט בדרום פילדלפיה. מטרו SEPTA (קו ברוד סטריט) עם תחנה סמוכה למתחם. גישה נוחה מהמרכז ומתחנת 30th Street (אמטרק). אזור ספורט נוח להליכה.",
    },
    {
        "name": "Mercedes-Benz Stadium", "city": "Atlanta", "country": "USA",
        "capacity": 75000, "latitude": 33.7553, "longitude": -84.4006,
        "year_built": 2017,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Mercedes-Benz_Stadium,_Jan_2018.jpg?width=800",
        "rating": 5, "expected_temp_celsius": 30.0, "city_attractiveness": 4,
        "review_en": "A technological marvel with its unique pinwheel retractable roof and massive 360-degree halo video board. One of the newest and most impressive stadiums in the world. Famously affordable concessions and a soccer-specific seating configuration make it a fan favorite.",
        "review_nl": "Een technologisch wonder met zijn unieke windmolen-uitschuifbaar dak en enorm 360-graden halo-videoscherm. Een van de nieuwste en meest indrukwekkende stadions ter wereld. Beroemd om de betaalbare horeca en een voetbalspecifieke stoelconfiguratie — een favoriet bij fans.",
        "review_pt": "Uma maravilha tecnológica com seu teto retrátil em formato de cata-vento e enorme telão de vídeo em 360 graus. Um dos estádios mais novos e impressionantes do mundo. Concessões famosamente acessíveis e configuração de assentos para futebol o tornam favorito dos torcedores.",
        "review_de": "Ein technologisches Wunderwerk mit seinem einzigartigen Windrad-Schiebedach und riesigem 360-Grad-Halo-Videoboard. Eines der neuesten und beeindruckendsten Stadien der Welt. Berühmt günstige Verpflegung und eine fußballspezifische Sitzanordnung machen es zum Fan-Favoriten.",
        "review_he": "פלא טכנולוגי עם גג נשלף ייחודי ומסך הילה ענק ב־360°. בין האצטדיונים החדשים והמרשימים בעולם. מזון במחירים סבירים וסידור מושבים מותאם לכדורגל — מועדף על אוהדים.",
        "accessibility_en": "Downtown Atlanta with MARTA rail (Vine City or GWCC stations). Walking distance from hotels and attractions. The city's transit is decent and ride-sharing is widely available. Hot and humid in summer — the retractable roof helps.",
        "accessibility_nl": "Centrum van Atlanta met MARTA-trein (stations Vine City of GWCC). Op loopafstand van hotels en attracties. Het openbaar vervoer van de stad is redelijk en ride-sharing is overal beschikbaar. Heet en vochtig in de zomer — het uitschuifbare dak helpt.",
        "accessibility_pt": "Centro de Atlanta com trem MARTA (estações Vine City ou GWCC). A uma curta caminhada de hotéis e atrações. O transporte público da cidade é decente e ride-sharing é amplamente disponível. Quente e úmido no verão — o teto retrátil ajuda.",
        "accessibility_de": "Innenstadt von Atlanta mit MARTA-Bahn (Stationen Vine City oder GWCC). Zu Fuß von Hotels und Sehenswürdigkeiten erreichbar. Der ÖPNV der Stadt ist ordentlich und Ride-Sharing weit verbreitet. Heiß und feucht im Sommer — das Schiebedach hilft.",
        "accessibility_he": "מרכז אטלנטה — רכבת MARTA (ויין סיטי או GWCC). במרחק הליכה ממלונות ואטרקציות. תחבורה סבירה והסעות בשיתוף נפוצות. קיץ חם ולח — הגג הנשלף עוזר.",
    },
    {
        "name": "SoFi Stadium", "city": "Inglewood", "country": "USA",
        "capacity": 70240, "latitude": 33.9535, "longitude": -118.3392,
        "year_built": 2020,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/SoFi_Stadium_2021.jpg?width=800",
        "rating": 5, "expected_temp_celsius": 24.0, "city_attractiveness": 5,
        "review_en": "The most expensive stadium ever built ($5.5 billion). A breathtaking indoor-outdoor design with a translucent ETFE roof. Host of Super Bowl LVI and the 2028 Olympics. The LA glamour factor is off the charts.",
        "review_nl": "Het duurste stadion ooit gebouwd ($5,5 miljard). Een adembenemend indoor-outdoor ontwerp met een doorschijnend ETFE-dak. Gastheer van Super Bowl LVI en de Olympische Spelen van 2028. De LA-glamourfactor is ongeëvenaard.",
        "review_pt": "O estádio mais caro já construído (US$ 5,5 bilhões). Um design interno-externo deslumbrante com teto translúcido de ETFE. Sede do Super Bowl LVI e das Olimpíadas de 2028. O fator glamour de LA está nas alturas.",
        "review_de": "Das teuerste Stadion, das je gebaut wurde (5,5 Milliarden Dollar). Ein atemberaubendes Indoor-Outdoor-Design mit einem lichtdurchlässigen ETFE-Dach. Gastgeber des Super Bowl LVI und der Olympischen Spiele 2028. Der LA-Glamour-Faktor ist beispiellos.",
        "review_he": "האצטדיון היקר ביותר שנבנה אי־פעם (כ־5.5 מיליארד דולר). עיצוב פנים־חוץ מרהיב עם גג ETFE שקוף לאור. אירח את סופרבול LVI ויארח את אולימפיאדת 2028. פקטור הגלמור של לוס אנג׳לס בשיאו.",
        "accessibility_en": "In Inglewood, near LAX airport. A new Metro K Line station is nearby. LA traffic is notoriously bad — ride-sharing or shuttles recommended. The surrounding area has been redeveloped with restaurants and entertainment.",
        "accessibility_nl": "In Inglewood, dicht bij luchthaven LAX. Een nieuw Metro K Line-station is in de buurt. LA-verkeer is berucht slecht — ride-sharing of pendeldiensten aanbevolen. De omgeving is herontwikkeld met restaurants en entertainment.",
        "accessibility_pt": "Em Inglewood, perto do aeroporto LAX. Uma nova estação da Metro K Line fica nas proximidades. O trânsito de LA é notoriamente ruim — ride-sharing ou shuttles recomendados. A área ao redor foi revitalizada com restaurantes e entretenimento.",
        "accessibility_de": "In Inglewood, nahe dem Flughafen LAX. Eine neue Metro K Line-Station ist in der Nähe. Der Verkehr in LA ist berüchtigt schlecht — Ride-Sharing oder Shuttles empfohlen. Die Umgebung wurde mit Restaurants und Unterhaltung neu gestaltet.",
        "accessibility_he": "באינגלווד, ליד נמל התעופה LAX. תחנת Metro K Line חדשה בקרבת מקום. הפקקים ב־LA קשים — מומלץ הסעה משותפת או שאטל. האזור חודש עם מסעדות ובילוי.",
    },
    {
        "name": "Levi's Stadium", "city": "Santa Clara", "country": "USA",
        "capacity": 68500, "latitude": 37.4032, "longitude": -121.9698,
        "year_built": 2014,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Levi%27s_Stadium_from_parking_lot.jpg?width=800",
        "rating": 4, "expected_temp_celsius": 24.0, "city_attractiveness": 5,
        "review_en": "A modern, tech-forward stadium in Silicon Valley. Great amenities and a clean design. The sun exposure on one side can be harsh for afternoon games, but the Bay Area location and pleasant climate are hard to beat.",
        "review_nl": "Een modern, technologisch geavanceerd stadion in Silicon Valley. Geweldige faciliteiten en een strak ontwerp. De zon aan één kant kan fel zijn bij middagwedstrijden, maar de locatie in de Bay Area en het aangename klimaat zijn moeilijk te overtreffen.",
        "review_pt": "Um estádio moderno e tecnologicamente avançado no Vale do Silício. Ótimas comodidades e design limpo. A exposição solar em um lado pode ser forte em jogos à tarde, mas a localização na Bay Area e o clima agradável são difíceis de superar.",
        "review_de": "Ein modernes, technikaffines Stadion im Silicon Valley. Tolle Annehmlichkeiten und ein klares Design. Die Sonnenexposition auf einer Seite kann bei Nachmittagsspielen hart sein, aber die Lage in der Bay Area und das angenehme Klima sind schwer zu schlagen.",
        "review_he": "אצטדיון מודרני וטכנולוגי בלב עמק הסיליקון. מתקנים מעולים ועיצוב נקי. חשיפה לשמש בצד אחד עלולה להיות קשה במשחקי אחר־צהריים, אך המיקום בביי אריה והאקלים הנעים מפצים.",
        "accessibility_en": "VTA light rail stops right at the stadium (Great America station). Caltrain connects to San Francisco. The South Bay has good freeway access but limited nightlife around the venue — SF is 45 min away by train.",
        "accessibility_nl": "VTA lightrail stopt direct bij het stadion (station Great America). Caltrain verbindt met San Francisco. De South Bay heeft goede snelwegtoegang maar beperkt uitgaansleven rond het stadion — SF is 45 min met de trein.",
        "accessibility_pt": "VTA light rail para bem no estádio (estação Great America). Caltrain conecta a São Francisco. O South Bay tem bom acesso rodoviário, mas vida noturna limitada perto do estádio — SF fica a 45 min de trem.",
        "accessibility_de": "VTA-Stadtbahn hält direkt am Stadion (Station Great America). Caltrain verbindet nach San Francisco. Die South Bay hat gute Autobahnanbindung, aber begrenztes Nachtleben um das Stadion — SF ist 45 Min. mit dem Zug entfernt.",
        "accessibility_he": "רכבת קלה VTA עוצרת ליד האצטדיון (גרייט אמריקה). קלטריין מחבר לסן פרנסיסקו. דרומית לביי יש גישה טובה לכבישים מהירים, פחות חיי לילה ליד האצטדיון — סן פרנסיסקו כ־45 דקות ברכבת.",
    },
    {
        "name": "Lumen Field", "city": "Seattle", "country": "USA",
        "capacity": 69000, "latitude": 47.5952, "longitude": -122.3316,
        "year_built": 2002,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/CenturyLink_Field_Seattle_WA.jpg?width=800",
        "rating": 4, "expected_temp_celsius": 20.0, "city_attractiveness": 4,
        "review_en": "Home of the Seattle Sounders and known as one of the loudest stadiums in the US. The partially covered roof amplifies crowd noise to incredible levels. Great views of the Seattle skyline and the mild Pacific Northwest climate is ideal for summer football.",
        "review_nl": "Thuisbasis van de Seattle Sounders en bekend als een van de luidste stadions van de VS. Het gedeeltelijk overdekte dak versterkt het publieklawaai tot ongelooflijke niveaus. Prachtig uitzicht op de skyline van Seattle en het milde klimaat van de Pacific Northwest is ideaal voor zomervoetbal.",
        "review_pt": "Casa do Seattle Sounders e conhecido como um dos estádios mais barulhentos dos EUA. O teto parcialmente coberto amplifica o barulho da torcida a níveis incríveis. Ótimas vistas do horizonte de Seattle e o clima ameno do noroeste do Pacífico é ideal para futebol de verão.",
        "review_de": "Heimat der Seattle Sounders und bekannt als eines der lautesten Stadien der USA. Das teilweise bedeckte Dach verstärkt den Publikumslärm auf unglaubliche Lautstärken. Tolle Aussichten auf die Skyline von Seattle und das milde Klima des pazifischen Nordwestens ist ideal für Sommerfußball.",
        "review_he": "ביתם של סיאטל סאונדרס, ידוע כאחד האצטדיונים הרועשים בארה״ב. הגג החלקי מגביר את רעש הקהל לרמות קיצוניות. נוף לסקייליין של סיאטל; האקלים הנוח בצפון־מערב השקט אידיאלי לכדורגל קיץ.",
        "accessibility_en": "Downtown Seattle with excellent transit. Link Light Rail, buses, and ferries are all nearby. Walking distance from Pike Place Market and the waterfront. One of the most accessible venues in the tournament.",
        "accessibility_nl": "Centrum van Seattle met uitstekend openbaar vervoer. Link Light Rail, bussen en veerboten zijn allemaal in de buurt. Op loopafstand van Pike Place Market en de waterkant. Een van de best bereikbare stadions van het toernooi.",
        "accessibility_pt": "Centro de Seattle com excelente transporte. Link Light Rail, ônibus e balsas ficam nas proximidades. A uma curta caminhada do Pike Place Market e da orla. Um dos estádios mais acessíveis do torneio.",
        "accessibility_de": "Innenstadt von Seattle mit hervorragendem ÖPNV. Link Light Rail, Busse und Fähren sind alle in der Nähe. Zu Fuß vom Pike Place Market und der Uferpromenade erreichbar. Einer der am besten erreichbaren Austragungsorte des Turniers.",
        "accessibility_he": "מרכז סיאטל עם תחבורה מצוינת. Link Light Rail, אוטובוסים ומעבורות בקרבת מקום. במרחק הליכה מפייק פלייס מרקט ומהטיילת. בין האצטדיונים הנגישים ביותר בטורניר.",
    },
    {
        "name": "NRG Stadium", "city": "Houston", "country": "USA",
        "capacity": 72220, "latitude": 29.6847, "longitude": -95.4107,
        "year_built": 2002,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Reliant_Stadium_Aerial.JPG?width=800",
        "rating": 3, "expected_temp_celsius": 33.0, "city_attractiveness": 3,
        "review_en": "A retractable-roof stadium essential for Houston's extreme summer heat. Functional and spacious but architecturally unremarkable. The roof will be crucial — Houston in June/July is swelteringly hot and humid. Good for events, but the surrounding area lacks character.",
        "review_nl": "Een stadion met uitschuifbaar dak, essentieel vanwege de extreme zomerhitte van Houston. Functioneel en ruim maar architectonisch onopvallend. Het dak is cruciaal — Houston is in juni/juli snikheet en vochtig. Goed voor evenementen, maar de omgeving mist karakter.",
        "review_pt": "Um estádio com teto retrátil essencial para o calor extremo do verão de Houston. Funcional e espaçoso, mas arquitetonicamente comum. O teto será crucial — Houston em junho/julho é escaldante e úmido. Bom para eventos, mas a área ao redor carece de personalidade.",
        "review_de": "Ein Stadion mit Schiebedach, unverzichtbar bei Houstons extremer Sommerhitze. Funktional und geräumig, aber architektonisch unspektakulär. Das Dach wird entscheidend sein — Houston ist im Juni/Juli drückend heiß und feucht. Gut für Veranstaltungen, aber die Umgebung hat wenig Charakter.",
        "review_he": "אצטדיון עם גג נשלף — חיוני בחום הקיץ הקיצוני של יוסטון. פונקציונלי ומרווח אך פחות מרשים אדריכלית. הגג קריטי — ביוני־יולי יוסטון לחה וצורבת. מתאים לאירועים; לסביבה פחות אופי מיוחד.",
        "accessibility_en": "Located in NRG Park, south of downtown Houston. METRORail has a stop nearby. Houston is very car-dependent — ride-sharing recommended. The heat makes walking uncomfortable; indoor connections help.",
        "accessibility_nl": "Gelegen in NRG Park, ten zuiden van het centrum van Houston. METRORail heeft een halte in de buurt. Houston is zeer autoafhankelijk — ride-sharing aanbevolen. De hitte maakt wandelen onaangenaam; overdekte verbindingen helpen.",
        "accessibility_pt": "Localizado no NRG Park, ao sul do centro de Houston. METRORail tem uma parada próxima. Houston é muito dependente de carros — ride-sharing recomendado. O calor torna caminhadas desconfortáveis; conexões internas ajudam.",
        "accessibility_de": "Im NRG Park südlich der Innenstadt von Houston gelegen. METRORail hat eine Haltestelle in der Nähe. Houston ist sehr autoabhängig — Ride-Sharing empfohlen. Die Hitze macht Gehen unangenehm; überdachte Verbindungen helfen.",
        "accessibility_he": "ב־NRG Park, דרומית למרכז יוסטון. METRORail עם תחנה סמוכה. העיר תלויה מאוד ברכב — מומלץ הסעה בשיתוף. החום מקשה על הליכה; מעברים מקורים עוזרים.",
    },
    {
        "name": "AT&T Stadium", "city": "Arlington", "country": "USA",
        "capacity": 80000, "latitude": 32.7473, "longitude": -97.0945,
        "year_built": 2009,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Arlington_June_2020_4_(AT%26T_Stadium).jpg?width=800",
        "rating": 5, "expected_temp_celsius": 34.0, "city_attractiveness": 4,
        "review_en": "Jerry Jones' palace — a colossal stadium with the world's largest column-free interior and a gigantic center-hung video board. The retractable roof and end-zone doors create a unique experience. Absolutely massive and impressive in every way.",
        "review_nl": "Het paleis van Jerry Jones — een kolossaal stadion met het grootste kolomvrije interieur ter wereld en een gigantisch centraal hangend videoscherm. Het uitschuifbare dak en de deuren in de eindzones creëren een unieke ervaring. Absoluut enorm en indrukwekkend in elk opzicht.",
        "review_pt": "O palácio de Jerry Jones — um estádio colossal com o maior interior sem colunas do mundo e um gigantesco telão central suspenso. O teto retrátil e as portas das end zones criam uma experiência única. Absolutamente massivo e impressionante em todos os aspectos.",
        "review_de": "Jerry Jones' Palast — ein kolossales Stadion mit dem größten stützenfreien Innenraum der Welt und einem gigantischen zentralen Videoboard. Das Schiebedach und die Endzonentore schaffen ein einzigartiges Erlebnis. In jeder Hinsicht absolut riesig und beeindruckend.",
        "review_he": "״ארמון״ ג׳רי ג׳ונס — אצטדיון ענק עם אולם פנימי ללא עמודים מהגדולים בעולם ומסך וידאו תלוי ענק. הגג הנשלף והשערים בקצה המגרש יוצרים חוויה ייחודית. מרשים ובולט בכל מימד.",
        "accessibility_en": "In Arlington, between Dallas and Fort Worth. No rail transit — car or shuttle required. TEXRail and TRE serve nearby stations but need a connection. Arlington has ample parking and flat terrain for walking between venues.",
        "accessibility_nl": "In Arlington, tussen Dallas en Fort Worth. Geen railverbinding — auto of pendeldienst vereist. TEXRail en TRE bedienen nabijgelegen stations maar vereisen een overstap. Arlington heeft ruime parkeerplaatsen en vlak terrein om tussen locaties te lopen.",
        "accessibility_pt": "Em Arlington, entre Dallas e Fort Worth. Sem transporte ferroviário — carro ou shuttle necessário. TEXRail e TRE atendem estações próximas, mas precisam de conexão. Arlington tem amplo estacionamento e terreno plano para caminhar entre locais.",
        "accessibility_de": "In Arlington, zwischen Dallas und Fort Worth. Kein Schienenverkehr — Auto oder Shuttle erforderlich. TEXRail und TRE bedienen nahegelegene Stationen, erfordern aber einen Umstieg. Arlington hat ausreichend Parkplätze und flaches Gelände zum Gehen zwischen den Spielstätten.",
        "accessibility_he": "בארלינגטון, בין דאלאס לפורט וורת׳. אין רכבת — נדרש רכב או שאטל. TEXRail ו־TRE לתחנות סמוכות עם החלפה. חניה בשפע ושטח שטוח לצעידה בין מתחמים.",
    },
    {
        "name": "Arrowhead Stadium", "city": "Kansas City", "country": "USA",
        "capacity": 76416, "latitude": 39.0489, "longitude": -94.4839,
        "year_built": 1972,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Aerial_view_of_Arrowhead_Stadium_08-31-2013_crop.jpg?width=800",
        "rating": 4, "expected_temp_celsius": 31.0, "city_attractiveness": 3,
        "review_en": "One of the loudest outdoor stadiums in the world, holding a Guinness record for crowd noise. A classic American football bowl with legendary tailgating culture. The stadium is older but well-maintained, and Kansas City's BBQ scene alone is worth the trip.",
        "review_nl": "Een van de luidste openluchtstadions ter wereld, met een Guinness-record voor publiekslawaai. Een klassieke American football-kom met een legendarische tailgate-cultuur. Het stadion is ouder maar goed onderhouden, en de BBQ-scene van Kansas City alleen al is de reis waard.",
        "review_pt": "Um dos estádios ao ar livre mais barulhentos do mundo, com recorde do Guinness para barulho de torcida. Uma clássica arena de futebol americano com cultura lendária de tailgating. O estádio é mais antigo, mas bem mantido, e a cena de BBQ de Kansas City por si só vale a viagem.",
        "review_de": "Eines der lautesten Freiluftstadien der Welt mit einem Guinness-Rekord für Publikumslärm. Eine klassische American-Football-Schüssel mit legendärer Tailgating-Kultur. Das Stadion ist älter, aber gut gepflegt, und Kansas Citys BBQ-Szene allein ist die Reise wert.",
        "review_he": "בין האצטדיונים הפתוחים הרועשים בעולם, עם שיא גינס לרעש קהל. ״קערה״ קלאסית לפוטבול אמריקאי ותרבות טיילגייט אגדית. האצטדיון מבוגר אך מטופח; סצנת ה־BBQ של קנזס סיטי שווה ביקור כשלעצמה.",
        "accessibility_en": "In the Truman Sports Complex, east of downtown KC. Car-dependent with massive parking lots. Shuttle services available on match days. Kansas City is spread out but has a growing streetcar line downtown.",
        "accessibility_nl": "In het Truman Sports Complex, ten oosten van het centrum van KC. Autoafhankelijk met enorme parkeerplaatsen. Pendeldiensten beschikbaar op wedstrijddagen. Kansas City is uitgestrekt maar heeft een groeiende tramlijn in het centrum.",
        "accessibility_pt": "No Truman Sports Complex, a leste do centro de KC. Dependente de carro com enormes estacionamentos. Serviços de shuttle disponíveis em dias de jogo. Kansas City é espalhada, mas tem uma linha de bonde em crescimento no centro.",
        "accessibility_de": "Im Truman Sports Complex, östlich der Innenstadt von KC. Autoabhängig mit riesigen Parkplätzen. Shuttlebusse an Spieltagen verfügbar. Kansas City ist weitläufig, hat aber eine wachsende Straßenbahnlinie in der Innenstadt.",
        "accessibility_he": "במתחם טרומן ספורטס, ממזרח למרכז קנזס סיטי. תלות ברכב וחניונות ענקיים. שאטלים בימי משחק. העיר מפוזרת אך קו חשמולית מתפתח במרכז.",
    },
    {
        "name": "Hard Rock Stadium", "city": "Miami Gardens", "country": "USA",
        "capacity": 65326, "latitude": 25.9580, "longitude": -80.2389,
        "year_built": 1987,
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Hard_Rock_Stadium_Prior_to_first_NFL_game.jpg?width=800",
        "rating": 4, "expected_temp_celsius": 31.0, "city_attractiveness": 5,
        "review_en": "Extensively renovated with a dramatic canopy roof that provides shade and captures the Miami vibe. Home to the Dolphins, host of multiple Super Bowls and the Miami Open. The tropical atmosphere and proximity to South Beach make it a glamorous venue.",
        "review_nl": "Uitgebreid gerenoveerd met een spectaculair baldakijndak dat schaduw biedt en de Miami-sfeer vangt. Thuisbasis van de Dolphins, gastheer van meerdere Super Bowls en de Miami Open. De tropische sfeer en nabijheid van South Beach maken het tot een glamoureuze locatie.",
        "review_pt": "Extensamente renovado com um teto em toldo dramático que fornece sombra e captura a vibe de Miami. Casa dos Dolphins, sede de múltiplos Super Bowls e do Miami Open. A atmosfera tropical e a proximidade com South Beach o tornam um local glamouroso.",
        "review_de": "Umfangreich renoviert mit einem dramatischen Baldachindach, das Schatten spendet und das Miami-Flair einfängt. Heimat der Dolphins, Gastgeber mehrerer Super Bowls und der Miami Open. Die tropische Atmosphäre und die Nähe zu South Beach machen es zu einem glamourösen Veranstaltungsort.",
        "review_he": "שופץ בהרחבה עם גג־צל דרמטי שולב את אווירת מיאמי. בית דולפינס, אירח סופרבולים ואת טורניר המיאמי אופן. אווירה טרופית וקרבה לסאות׳ ביץ׳ — מתחם גלאמורי.",
        "accessibility_en": "In Miami Gardens, north of downtown Miami. Tri-Rail commuter trains and express bus routes on match days. Miami traffic can be challenging but ride-sharing is excellent. The beach, nightlife, and hotel options in greater Miami are world-class.",
        "accessibility_nl": "In Miami Gardens, ten noorden van het centrum van Miami. Tri-Rail-forensentreinen en expresbuslijnen op wedstrijddagen. Miami-verkeer kan uitdagend zijn, maar ride-sharing is uitstekend. Het strand, nachtleven en hotelaanbod in groot-Miami zijn van wereldklasse.",
        "accessibility_pt": "Em Miami Gardens, ao norte do centro de Miami. Trens suburbanos Tri-Rail e linhas de ônibus expresso em dias de jogo. O trânsito de Miami pode ser desafiador, mas ride-sharing é excelente. A praia, vida noturna e opções de hotéis na grande Miami são de classe mundial.",
        "accessibility_de": "In Miami Gardens, nördlich der Innenstadt von Miami. Tri-Rail-Pendlerzüge und Express-Buslinien an Spieltagen. Miamis Verkehr kann herausfordernd sein, aber Ride-Sharing ist ausgezeichnet. Strand, Nachtleben und Hoteloptionen im Großraum Miami sind Weltklasse.",
        "accessibility_he": "במיאמי גארדנס, צפונית למרכז מיאמי. רכבות פרברים Tri-Rail וקווי אוטובוס מהירים בימי משחק. התנועה מאתגרת אך אפליקציות הסעה מצוינות. חוף, חיי לילה ומלונות במטרופולין — ברמה עולמית.",
    },
]

from venue_locales_es_it import merge_into_venues

merge_into_venues(VENUES)

# ---------------------------------------------------------------------------
# Teams (48 qualified teams with approximate FIFA rankings)
# ---------------------------------------------------------------------------
TEAMS = [
    {"name": "Mexico", "fifa_code": "MEX", "group_letter": "A", "world_ranking": 14},
    {"name": "South Africa", "fifa_code": "RSA", "group_letter": "A", "world_ranking": 59},
    {"name": "South Korea", "fifa_code": "KOR", "group_letter": "A", "world_ranking": 22},
    {"name": "Czechia", "fifa_code": "CZE", "group_letter": "A", "world_ranking": 36},
    {"name": "Canada", "fifa_code": "CAN", "group_letter": "B", "world_ranking": 48},
    {"name": "Bosnia and Herzegovina", "fifa_code": "BIH", "group_letter": "B", "world_ranking": 62},
    {"name": "Qatar", "fifa_code": "QAT", "group_letter": "B", "world_ranking": 35},
    {"name": "Switzerland", "fifa_code": "SUI", "group_letter": "B", "world_ranking": 15},
    {"name": "Brazil", "fifa_code": "BRA", "group_letter": "C", "world_ranking": 5},
    {"name": "Morocco", "fifa_code": "MAR", "group_letter": "C", "world_ranking": 13},
    {"name": "Haiti", "fifa_code": "HAI", "group_letter": "C", "world_ranking": 88},
    {"name": "Scotland", "fifa_code": "SCO", "group_letter": "C", "world_ranking": 39},
    {"name": "United States", "fifa_code": "USA", "group_letter": "D", "world_ranking": 11},
    {"name": "Paraguay", "fifa_code": "PAR", "group_letter": "D", "world_ranking": 52},
    {"name": "Australia", "fifa_code": "AUS", "group_letter": "D", "world_ranking": 24},
    {"name": "Türkiye", "fifa_code": "TUR", "group_letter": "D", "world_ranking": 26},
    {"name": "Germany", "fifa_code": "GER", "group_letter": "E", "world_ranking": 3},
    {"name": "Curaçao", "fifa_code": "CUW", "group_letter": "E", "world_ranking": 87},
    {"name": "Côte d'Ivoire", "fifa_code": "CIV", "group_letter": "E", "world_ranking": 40},
    {"name": "Ecuador", "fifa_code": "ECU", "group_letter": "E", "world_ranking": 30},
    {"name": "Netherlands", "fifa_code": "NED", "group_letter": "F", "world_ranking": 7},
    {"name": "Japan", "fifa_code": "JPN", "group_letter": "F", "world_ranking": 17},
    {"name": "Sweden", "fifa_code": "SWE", "group_letter": "F", "world_ranking": 41},
    {"name": "Tunisia", "fifa_code": "TUN", "group_letter": "F", "world_ranking": 37},
    {"name": "Belgium", "fifa_code": "BEL", "group_letter": "G", "world_ranking": 6},
    {"name": "Egypt", "fifa_code": "EGY", "group_letter": "G", "world_ranking": 33},
    {"name": "Iran", "fifa_code": "IRN", "group_letter": "G", "world_ranking": 21},
    {"name": "New Zealand", "fifa_code": "NZL", "group_letter": "G", "world_ranking": 93},
    {"name": "Spain", "fifa_code": "ESP", "group_letter": "H", "world_ranking": 1},
    {"name": "Cape Verde", "fifa_code": "CPV", "group_letter": "H", "world_ranking": 65},
    {"name": "Saudi Arabia", "fifa_code": "KSA", "group_letter": "H", "world_ranking": 56},
    {"name": "Uruguay", "fifa_code": "URU", "group_letter": "H", "world_ranking": 10},
    {"name": "France", "fifa_code": "FRA", "group_letter": "I", "world_ranking": 2},
    {"name": "Senegal", "fifa_code": "SEN", "group_letter": "I", "world_ranking": 20},
    {"name": "Iraq", "fifa_code": "IRQ", "group_letter": "I", "world_ranking": 55},
    {"name": "Norway", "fifa_code": "NOR", "group_letter": "I", "world_ranking": 44},
    {"name": "Argentina", "fifa_code": "ARG", "group_letter": "J", "world_ranking": 4},
    {"name": "Algeria", "fifa_code": "ALG", "group_letter": "J", "world_ranking": 34},
    {"name": "Austria", "fifa_code": "AUT", "group_letter": "J", "world_ranking": 25},
    {"name": "Jordan", "fifa_code": "JOR", "group_letter": "J", "world_ranking": 68},
    {"name": "Portugal", "fifa_code": "POR", "group_letter": "K", "world_ranking": 8},
    {"name": "DR Congo", "fifa_code": "COD", "group_letter": "K", "world_ranking": 60},
    {"name": "Uzbekistan", "fifa_code": "UZB", "group_letter": "K", "world_ranking": 63},
    {"name": "Colombia", "fifa_code": "COL", "group_letter": "K", "world_ranking": 12},
    {"name": "England", "fifa_code": "ENG", "group_letter": "L", "world_ranking": 9},
    {"name": "Croatia", "fifa_code": "CRO", "group_letter": "L", "world_ranking": 16},
    {"name": "Ghana", "fifa_code": "GHA", "group_letter": "L", "world_ranking": 64},
    {"name": "Panama", "fifa_code": "PAN", "group_letter": "L", "world_ranking": 45},
]

for t in TEAMS:
    code_map = {
        "MEX": "mx", "RSA": "za", "KOR": "kr", "CZE": "cz",
        "CAN": "ca", "BIH": "ba", "QAT": "qa", "SUI": "ch",
        "BRA": "br", "MAR": "ma", "HAI": "ht", "SCO": "gb-sct",
        "USA": "us", "PAR": "py", "AUS": "au", "TUR": "tr",
        "GER": "de", "CUW": "cw", "CIV": "ci", "ECU": "ec",
        "NED": "nl", "JPN": "jp", "SWE": "se", "TUN": "tn",
        "BEL": "be", "EGY": "eg", "IRN": "ir", "NZL": "nz",
        "ESP": "es", "CPV": "cv", "KSA": "sa", "URU": "uy",
        "FRA": "fr", "SEN": "sn", "IRQ": "iq", "NOR": "no",
        "ARG": "ar", "ALG": "dz", "AUT": "at", "JOR": "jo",
        "POR": "pt", "COD": "cd", "UZB": "uz", "COL": "co",
        "ENG": "gb-eng", "CRO": "hr", "GHA": "gh", "PAN": "pa",
    }
    cc = code_map.get(t["fifa_code"], "xx")
    t["flag_url"] = f"https://flagcdn.com/w80/{cc}.png"


def _utc(month, day, hour, minute=0):
    """Eastern Time to UTC (ET = UTC-4 during DST in June/July)."""
    from datetime import timedelta
    et = datetime(2026, month, day, hour, minute, tzinfo=timezone.utc)
    return et + timedelta(hours=4)


# ---------------------------------------------------------------------------
# Group stage matches (72 matches, numbers 1-72)
# ---------------------------------------------------------------------------
GROUP_MATCHES = [
    {"mn": 1, "stage": "group", "gl": "A", "home": "MEX", "away": "RSA", "venue": "Estadio Azteca", "ko": _utc(6, 11, 15)},
    {"mn": 2, "stage": "group", "gl": "A", "home": "KOR", "away": "CZE", "venue": "Estadio Akron", "ko": _utc(6, 11, 22)},
    {"mn": 3, "stage": "group", "gl": "A", "home": "CZE", "away": "RSA", "venue": "Mercedes-Benz Stadium", "ko": _utc(6, 18, 12)},
    {"mn": 4, "stage": "group", "gl": "A", "home": "MEX", "away": "KOR", "venue": "Estadio Akron", "ko": _utc(6, 18, 21)},
    {"mn": 5, "stage": "group", "gl": "A", "home": "CZE", "away": "MEX", "venue": "Estadio Azteca", "ko": _utc(6, 24, 21)},
    {"mn": 6, "stage": "group", "gl": "A", "home": "RSA", "away": "KOR", "venue": "Estadio BBVA", "ko": _utc(6, 24, 21)},
    {"mn": 7, "stage": "group", "gl": "B", "home": "CAN", "away": "BIH", "venue": "BMO Field", "ko": _utc(6, 12, 15)},
    {"mn": 8, "stage": "group", "gl": "B", "home": "QAT", "away": "SUI", "venue": "Levi's Stadium", "ko": _utc(6, 13, 15)},
    {"mn": 9, "stage": "group", "gl": "B", "home": "SUI", "away": "BIH", "venue": "SoFi Stadium", "ko": _utc(6, 18, 15)},
    {"mn": 10, "stage": "group", "gl": "B", "home": "CAN", "away": "QAT", "venue": "BC Place", "ko": _utc(6, 18, 18)},
    {"mn": 11, "stage": "group", "gl": "B", "home": "SUI", "away": "CAN", "venue": "BC Place", "ko": _utc(6, 24, 15)},
    {"mn": 12, "stage": "group", "gl": "B", "home": "BIH", "away": "QAT", "venue": "Lumen Field", "ko": _utc(6, 24, 15)},
    {"mn": 13, "stage": "group", "gl": "C", "home": "BRA", "away": "MAR", "venue": "MetLife Stadium", "ko": _utc(6, 13, 18)},
    {"mn": 14, "stage": "group", "gl": "C", "home": "HAI", "away": "SCO", "venue": "Gillette Stadium", "ko": _utc(6, 13, 21)},
    {"mn": 15, "stage": "group", "gl": "C", "home": "SCO", "away": "MAR", "venue": "Gillette Stadium", "ko": _utc(6, 19, 18)},
    {"mn": 16, "stage": "group", "gl": "C", "home": "BRA", "away": "HAI", "venue": "Lincoln Financial Field", "ko": _utc(6, 19, 21)},
    {"mn": 17, "stage": "group", "gl": "C", "home": "SCO", "away": "BRA", "venue": "Hard Rock Stadium", "ko": _utc(6, 24, 18)},
    {"mn": 18, "stage": "group", "gl": "C", "home": "MAR", "away": "HAI", "venue": "Mercedes-Benz Stadium", "ko": _utc(6, 24, 18)},
    {"mn": 19, "stage": "group", "gl": "D", "home": "USA", "away": "PAR", "venue": "SoFi Stadium", "ko": _utc(6, 12, 21)},
    {"mn": 20, "stage": "group", "gl": "D", "home": "AUS", "away": "TUR", "venue": "BC Place", "ko": _utc(6, 13, 0)},
    {"mn": 21, "stage": "group", "gl": "D", "home": "TUR", "away": "PAR", "venue": "Levi's Stadium", "ko": _utc(6, 19, 0)},
    {"mn": 22, "stage": "group", "gl": "D", "home": "USA", "away": "AUS", "venue": "Lumen Field", "ko": _utc(6, 19, 15)},
    {"mn": 23, "stage": "group", "gl": "D", "home": "TUR", "away": "USA", "venue": "SoFi Stadium", "ko": _utc(6, 25, 22)},
    {"mn": 24, "stage": "group", "gl": "D", "home": "PAR", "away": "AUS", "venue": "Levi's Stadium", "ko": _utc(6, 25, 22)},
    {"mn": 25, "stage": "group", "gl": "E", "home": "GER", "away": "CUW", "venue": "NRG Stadium", "ko": _utc(6, 14, 13)},
    {"mn": 26, "stage": "group", "gl": "E", "home": "CIV", "away": "ECU", "venue": "Lincoln Financial Field", "ko": _utc(6, 14, 19)},
    {"mn": 27, "stage": "group", "gl": "E", "home": "GER", "away": "CIV", "venue": "BMO Field", "ko": _utc(6, 20, 16)},
    {"mn": 28, "stage": "group", "gl": "E", "home": "ECU", "away": "CUW", "venue": "Arrowhead Stadium", "ko": _utc(6, 20, 20)},
    {"mn": 29, "stage": "group", "gl": "E", "home": "ECU", "away": "GER", "venue": "MetLife Stadium", "ko": _utc(6, 25, 16)},
    {"mn": 30, "stage": "group", "gl": "E", "home": "CUW", "away": "CIV", "venue": "Lincoln Financial Field", "ko": _utc(6, 25, 16)},
    {"mn": 31, "stage": "group", "gl": "F", "home": "NED", "away": "JPN", "venue": "AT&T Stadium", "ko": _utc(6, 14, 16)},
    {"mn": 32, "stage": "group", "gl": "F", "home": "SWE", "away": "TUN", "venue": "Estadio BBVA", "ko": _utc(6, 14, 22)},
    {"mn": 33, "stage": "group", "gl": "F", "home": "NED", "away": "SWE", "venue": "NRG Stadium", "ko": _utc(6, 20, 13)},
    {"mn": 34, "stage": "group", "gl": "F", "home": "TUN", "away": "JPN", "venue": "Estadio BBVA", "ko": _utc(6, 20, 0)},
    {"mn": 35, "stage": "group", "gl": "F", "home": "TUN", "away": "NED", "venue": "AT&T Stadium", "ko": _utc(6, 25, 19)},
    {"mn": 36, "stage": "group", "gl": "F", "home": "JPN", "away": "SWE", "venue": "Arrowhead Stadium", "ko": _utc(6, 25, 19)},
    {"mn": 37, "stage": "group", "gl": "G", "home": "BEL", "away": "EGY", "venue": "Lumen Field", "ko": _utc(6, 15, 15)},
    {"mn": 38, "stage": "group", "gl": "G", "home": "IRN", "away": "NZL", "venue": "SoFi Stadium", "ko": _utc(6, 15, 21)},
    {"mn": 39, "stage": "group", "gl": "G", "home": "BEL", "away": "IRN", "venue": "SoFi Stadium", "ko": _utc(6, 21, 15)},
    {"mn": 40, "stage": "group", "gl": "G", "home": "NZL", "away": "EGY", "venue": "BC Place", "ko": _utc(6, 21, 21)},
    {"mn": 41, "stage": "group", "gl": "G", "home": "NZL", "away": "BEL", "venue": "BC Place", "ko": _utc(6, 26, 23)},
    {"mn": 42, "stage": "group", "gl": "G", "home": "EGY", "away": "IRN", "venue": "Lumen Field", "ko": _utc(6, 26, 23)},
    {"mn": 43, "stage": "group", "gl": "H", "home": "ESP", "away": "CPV", "venue": "Mercedes-Benz Stadium", "ko": _utc(6, 15, 12)},
    {"mn": 44, "stage": "group", "gl": "H", "home": "KSA", "away": "URU", "venue": "Hard Rock Stadium", "ko": _utc(6, 15, 18)},
    {"mn": 45, "stage": "group", "gl": "H", "home": "ESP", "away": "KSA", "venue": "Mercedes-Benz Stadium", "ko": _utc(6, 21, 12)},
    {"mn": 46, "stage": "group", "gl": "H", "home": "URU", "away": "CPV", "venue": "Hard Rock Stadium", "ko": _utc(6, 21, 18)},
    {"mn": 47, "stage": "group", "gl": "H", "home": "URU", "away": "ESP", "venue": "NRG Stadium", "ko": _utc(6, 26, 20)},
    {"mn": 48, "stage": "group", "gl": "H", "home": "CPV", "away": "KSA", "venue": "Estadio Akron", "ko": _utc(6, 26, 20)},
    {"mn": 49, "stage": "group", "gl": "I", "home": "FRA", "away": "SEN", "venue": "MetLife Stadium", "ko": _utc(6, 16, 15)},
    {"mn": 50, "stage": "group", "gl": "I", "home": "IRQ", "away": "NOR", "venue": "Gillette Stadium", "ko": _utc(6, 16, 18)},
    {"mn": 51, "stage": "group", "gl": "I", "home": "FRA", "away": "IRQ", "venue": "Lincoln Financial Field", "ko": _utc(6, 22, 17)},
    {"mn": 52, "stage": "group", "gl": "I", "home": "NOR", "away": "SEN", "venue": "MetLife Stadium", "ko": _utc(6, 22, 20)},
    {"mn": 53, "stage": "group", "gl": "I", "home": "NOR", "away": "FRA", "venue": "Gillette Stadium", "ko": _utc(6, 26, 15)},
    {"mn": 54, "stage": "group", "gl": "I", "home": "SEN", "away": "IRQ", "venue": "BMO Field", "ko": _utc(6, 26, 15)},
    {"mn": 55, "stage": "group", "gl": "J", "home": "ARG", "away": "ALG", "venue": "Arrowhead Stadium", "ko": _utc(6, 16, 21)},
    {"mn": 56, "stage": "group", "gl": "J", "home": "AUT", "away": "JOR", "venue": "Levi's Stadium", "ko": _utc(6, 17, 0)},
    {"mn": 57, "stage": "group", "gl": "J", "home": "ARG", "away": "AUT", "venue": "AT&T Stadium", "ko": _utc(6, 22, 13)},
    {"mn": 58, "stage": "group", "gl": "J", "home": "JOR", "away": "ALG", "venue": "Levi's Stadium", "ko": _utc(6, 22, 23)},
    {"mn": 59, "stage": "group", "gl": "J", "home": "JOR", "away": "ARG", "venue": "AT&T Stadium", "ko": _utc(6, 27, 22)},
    {"mn": 60, "stage": "group", "gl": "J", "home": "ALG", "away": "AUT", "venue": "Arrowhead Stadium", "ko": _utc(6, 27, 22)},
    {"mn": 61, "stage": "group", "gl": "K", "home": "POR", "away": "COD", "venue": "NRG Stadium", "ko": _utc(6, 17, 13)},
    {"mn": 62, "stage": "group", "gl": "K", "home": "UZB", "away": "COL", "venue": "Estadio Azteca", "ko": _utc(6, 17, 22)},
    {"mn": 63, "stage": "group", "gl": "K", "home": "POR", "away": "UZB", "venue": "NRG Stadium", "ko": _utc(6, 23, 13)},
    {"mn": 64, "stage": "group", "gl": "K", "home": "COL", "away": "COD", "venue": "Estadio Akron", "ko": _utc(6, 23, 22)},
    {"mn": 65, "stage": "group", "gl": "K", "home": "COL", "away": "POR", "venue": "Hard Rock Stadium", "ko": _utc(6, 27, 19, 30)},
    {"mn": 66, "stage": "group", "gl": "K", "home": "COD", "away": "UZB", "venue": "Mercedes-Benz Stadium", "ko": _utc(6, 27, 19, 30)},
    {"mn": 67, "stage": "group", "gl": "L", "home": "ENG", "away": "CRO", "venue": "AT&T Stadium", "ko": _utc(6, 17, 16)},
    {"mn": 68, "stage": "group", "gl": "L", "home": "GHA", "away": "PAN", "venue": "BMO Field", "ko": _utc(6, 17, 19)},
    {"mn": 69, "stage": "group", "gl": "L", "home": "ENG", "away": "GHA", "venue": "Gillette Stadium", "ko": _utc(6, 23, 16)},
    {"mn": 70, "stage": "group", "gl": "L", "home": "PAN", "away": "CRO", "venue": "BMO Field", "ko": _utc(6, 23, 19)},
    {"mn": 71, "stage": "group", "gl": "L", "home": "PAN", "away": "ENG", "venue": "MetLife Stadium", "ko": _utc(6, 27, 17)},
    {"mn": 72, "stage": "group", "gl": "L", "home": "CRO", "away": "GHA", "venue": "Lincoln Financial Field", "ko": _utc(6, 27, 17)},
]

KNOCKOUT_MATCHES = [
    {"mn": 73, "stage": "round_of_32", "venue": "SoFi Stadium", "ko": _utc(6, 28, 20)},
    {"mn": 74, "stage": "round_of_32", "venue": "NRG Stadium", "ko": _utc(6, 29, 18)},
    {"mn": 75, "stage": "round_of_32", "venue": "Gillette Stadium", "ko": _utc(6, 29, 21, 30)},
    {"mn": 76, "stage": "round_of_32", "venue": "Estadio BBVA", "ko": _utc(6, 30, 2)},
    {"mn": 77, "stage": "round_of_32", "venue": "AT&T Stadium", "ko": _utc(6, 30, 18)},
    {"mn": 78, "stage": "round_of_32", "venue": "MetLife Stadium", "ko": _utc(6, 30, 22)},
    {"mn": 79, "stage": "round_of_32", "venue": "Estadio Azteca", "ko": _utc(7, 1, 2)},
    {"mn": 80, "stage": "round_of_32", "venue": "Mercedes-Benz Stadium", "ko": _utc(7, 1, 17)},
    {"mn": 81, "stage": "round_of_32", "venue": "Lumen Field", "ko": _utc(7, 1, 21)},
    {"mn": 82, "stage": "round_of_32", "venue": "Levi's Stadium", "ko": _utc(7, 2, 17)},
    {"mn": 83, "stage": "round_of_32", "venue": "BC Place", "ko": _utc(7, 2, 17)},
    {"mn": 84, "stage": "round_of_32", "venue": "BMO Field", "ko": _utc(7, 2, 21)},
    {"mn": 85, "stage": "round_of_32", "venue": "AT&T Stadium", "ko": _utc(7, 3, 17)},
    {"mn": 86, "stage": "round_of_32", "venue": "SoFi Stadium", "ko": _utc(7, 3, 17)},
    {"mn": 87, "stage": "round_of_32", "venue": "Hard Rock Stadium", "ko": _utc(7, 3, 21)},
    {"mn": 88, "stage": "round_of_32", "venue": "Arrowhead Stadium", "ko": _utc(7, 3, 21)},
    {"mn": 89, "stage": "round_of_16", "venue": "Lincoln Financial Field", "ko": _utc(7, 4, 17)},
    {"mn": 90, "stage": "round_of_16", "venue": "NRG Stadium", "ko": _utc(7, 4, 13)},
    {"mn": 91, "stage": "round_of_16", "venue": "MetLife Stadium", "ko": _utc(7, 5, 17)},
    {"mn": 92, "stage": "round_of_16", "venue": "Estadio Azteca", "ko": _utc(7, 5, 21)},
    {"mn": 93, "stage": "round_of_16", "venue": "AT&T Stadium", "ko": _utc(7, 6, 17)},
    {"mn": 94, "stage": "round_of_16", "venue": "Lumen Field", "ko": _utc(7, 6, 17)},
    {"mn": 95, "stage": "round_of_16", "venue": "Mercedes-Benz Stadium", "ko": _utc(7, 7, 17)},
    {"mn": 96, "stage": "round_of_16", "venue": "BC Place", "ko": _utc(7, 7, 17)},
    {"mn": 97, "stage": "quarter_final", "venue": "Gillette Stadium", "ko": _utc(7, 9, 15)},
    {"mn": 98, "stage": "quarter_final", "venue": "SoFi Stadium", "ko": _utc(7, 10, 15)},
    {"mn": 99, "stage": "quarter_final", "venue": "Hard Rock Stadium", "ko": _utc(7, 11, 15)},
    {"mn": 100, "stage": "quarter_final", "venue": "Arrowhead Stadium", "ko": _utc(7, 11, 21)},
    {"mn": 101, "stage": "semi_final", "venue": "AT&T Stadium", "ko": _utc(7, 14, 15)},
    {"mn": 102, "stage": "semi_final", "venue": "Mercedes-Benz Stadium", "ko": _utc(7, 15, 15)},
    {"mn": 103, "stage": "third_place", "venue": "Hard Rock Stadium", "ko": _utc(7, 18, 17)},
    {"mn": 104, "stage": "final", "venue": "MetLife Stadium", "ko": _utc(7, 19, 15)},
]

# ---------------------------------------------------------------------------
# Fun comments — imported from match_comments.py (unique per game)
# ---------------------------------------------------------------------------
from fun_comment_locales import locales_for_comment_bundle
from match_comments import (
    MATCH_COMMENTS,
    KNOCKOUT_MATCH_COMMENTS,
    KNOCKOUT_TEMPLATES,
    ALL_STYLE_NAMES,
)



def seed():
    print("Creating tables...")
    import app.models  # noqa: F401 — Subgroup etc. must be registered before create_all

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.query(Team).count() > 0:
            print("Database already seeded. Skipping.")
            return

        # Venues
        print("Seeding venues...")
        venue_map: dict[str, Venue] = {}
        for v in VENUES:
            venue = Venue(**v)
            db.add(venue)
            db.flush()
            venue_map[v["name"]] = venue

        # Teams
        print("Seeding teams...")
        team_map: dict[str, Team] = {}
        for t in TEAMS:
            profile = build_team_profile(
                t["name"],
                t["fifa_code"],
                t["group_letter"],
                t["world_ranking"],
            )
            team = Team(**t, **profile)
            db.add(team)
            db.flush()
            team_map[t["fifa_code"]] = team
            for player in build_team_squad(t["fifa_code"], t["name"], t["world_ranking"]):
                db.add(TeamPlayer(team_id=team.id, **player))

        # Group matches
        print("Seeding group stage matches...")
        match_objects: dict[int, Match] = {}
        for gm in GROUP_MATCHES:
            m = Match(
                match_number=gm["mn"],
                stage=gm["stage"],
                group_letter=gm["gl"],
                home_team_id=team_map[gm["home"]].id,
                away_team_id=team_map[gm["away"]].id,
                venue_id=venue_map[gm["venue"]].id,
                kickoff_utc=gm["ko"],
                status="upcoming",
            )
            db.add(m)
            db.flush()
            match_objects[gm["mn"]] = m

        # Knockout matches
        print("Seeding knockout matches...")
        for km in KNOCKOUT_MATCHES:
            m = Match(
                match_number=km["mn"],
                stage=km["stage"],
                group_letter=None,
                home_team_id=None,
                away_team_id=None,
                venue_id=venue_map[km["venue"]].id,
                kickoff_utc=km["ko"],
                status="upcoming",
            )
            db.add(m)
            db.flush()
            match_objects[km["mn"]] = m

        # Fun comments (unique per group match, templates for knockout)
        print("Seeding fun comments...")
        random.seed(2026)
        comment_count = 0
        for mn, m in match_objects.items():
            if mn in MATCH_COMMENTS:
                c = MATCH_COMMENTS[mn]
                text_it, text_es = locales_for_comment_bundle(c)
                db.add(FunComment(
                    match_id=m.id,
                    comment_text=c["en"],
                    comment_text_nl=c["nl"],
                    comment_text_pt=c["pt"],
                    comment_text_de=c["de"],
                    comment_text_it=text_it,
                    comment_text_es=text_es,
                    style=c["style"],
                ))
                comment_count += 1
            elif mn in KNOCKOUT_MATCH_COMMENTS:
                c = KNOCKOUT_MATCH_COMMENTS[mn]
                text_it, text_es = locales_for_comment_bundle(c)
                db.add(FunComment(
                    match_id=m.id,
                    comment_text=c["en"],
                    comment_text_nl=c["nl"],
                    comment_text_pt=c["pt"],
                    comment_text_de=c["de"],
                    comment_text_it=text_it,
                    comment_text_es=text_es,
                    style=c["style"],
                ))
                comment_count += 1
            elif m.home_team_id is None:
                style = random.choice(ALL_STYLE_NAMES)
                tmpl = KNOCKOUT_TEMPLATES.get(style, KNOCKOUT_TEMPLATES["lineker"])
                text_it, text_es = locales_for_comment_bundle(tmpl)
                db.add(FunComment(
                    match_id=m.id,
                    comment_text=tmpl["en"],
                    comment_text_nl=tmpl["nl"],
                    comment_text_pt=tmpl["pt"],
                    comment_text_de=tmpl["de"],
                    comment_text_it=text_it,
                    comment_text_es=text_es,
                    style=style,
                ))
                comment_count += 1

        # Admin user
        print("Creating admin user...")
        admin = User(
            username="admin",
            email="admin@wkpoule.com",
            password_hash=hash_password("admin123"),
            is_admin=True,
            include_in_rankings=False,
        )
        db.add(admin)

        db.commit()
        print(f"Seeded {len(VENUES)} venues, {len(TEAMS)} teams, "
              f"{len(GROUP_MATCHES) + len(KNOCKOUT_MATCHES)} matches, "
              f"{comment_count} fun comments, 1 admin user.")
        print("Done!")
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
