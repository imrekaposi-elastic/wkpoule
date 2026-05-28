"""
Expert analyst voice updates for wkpoule match comments.

Replaces selected group-stage and knockout entries with new analyst styles:
balotelli, kahn, gascoigne, crouch, joaquin.

Apply via apply_analyst_updates() against MATCH_COMMENTS and KNOCKOUT_MATCH_COMMENTS dicts.
"""

KNOCKOUT_TEMPLATES_NEW = {
    "balotelli": {
        "en": "Knockout football — no more hiding, no more excuses. One team walks out famous, the other walks out asking why always them. I love this stage: chaos, pressure, and someone pretending they are calm while their heart is screaming. Beautiful madness.",
        "nl": "Knock-outvoetbal — geen schuilplaats meer, geen smoesjes meer. Het ene team vertrekt beroemd, het andere vertrekt met de vraag: waarom altijd wij. Ik hou van dit stadium: chaos, druk, en iemand die doet alsof hij kalm is terwijl zijn hart schreeuwt. Prachtige waanzin.",
        "pt": "Futebol eliminatório — sem mais esconderijo, sem mais desculpas. Um time sai famoso, o outro sai perguntando por que sempre eles. Eu amo essa fase: caos, pressão e alguém fingindo calma enquanto o coração grita. Loucura linda.",
        "de": "K.o.-Fußball — kein Verstecken mehr, keine Ausreden mehr. Ein Team geht berühmt raus, das andere geht raus und fragt: warum immer wir. Ich liebe diese Phase: Chaos, Druck, und jemand tut so, als wäre er ruhig, während das Herz schreit. Schöner Wahnsinn.",
    },
    "kahn": {
        "en": "Knockout round. The air changes — every breath costs courage. In my box there was only command: shout, organise, punish hesitation. Tonight two armies meet and one will leave broken. No mercy. No second life. Only who stands when the whistle ends.",
        "nl": "Knock-outronde. De lucht verandert — elke ademteug kost moed. In mijn zestien meter gold alleen bevel: schreeuw, organiseer, straaf aarzeling. Vanavond botsen twee legers en één vertrekt gebroken. Geen genade. Geen tweede leven. Alleen wie staat als het fluitsignaal klinkt.",
        "pt": "Fase eliminatória. O ar muda — cada respiração custa coragem. Na minha área só valia comando: gritar, organizar, punir hesitação. Hoje dois exércitos se encontram e um sai quebrado. Sem piedade. Sem segunda vida. Só quem fica de pé quando o apito acaba.",
        "de": "K.o.-Runde. Die Luft wechselt — jeder Atemzug kostet Mut. In meinem Sechzehn galt nur Befehl: brüllen, ordnen, Zögern bestrafen. Heute treffen zwei Armeen aufeinander, und eines geht gebrochen. Keine Gnade. Kein zweites Leben. Nur wer steht, wenn der Pfiff endet.",
    },
    "gascoigne": {
        "en": "Knockout night, mate — this is where football stops being maths and starts being feeling. You can train all week, but when the crowd roars your legs remember who you were as a kid. Win or lose, you leave something honest on that grass. That's the game I fell for.",
        "nl": "Knock-outavond, maat — hier stopt voetbal met rekenen en begint het met voelen. Je kunt de hele week trainen, maar als het publiek brult herinneren je benen wie je als kind was. Win of verlies, je laat iets eerlijks achter op dat gras. Daar werd ik verliefd op dit spel.",
        "pt": "Noite de mata-mata, parceiro — aqui o futebol deixa de ser conta e vira sentimento. Você treina a semana inteira, mas quando a torcida ruge as pernas lembram quem você era criança. Ganhe ou perca, você deixa algo honesto nesse gramado. Foi por isso que me apaixonei.",
        "de": "K.o.-Abend, Kumpel — hier hört Fußball auf zu rechnen und fängt an zu fühlen. Du kannst die ganze Woche trainieren, aber wenn die Menge brüllt, erinnern deine Beine, wer du als Kind warst. Sieg oder Niederlage — du lässt etwas Ehrliches auf diesem Rasen. Dafür liebe ich das Spiel.",
    },
    "crouch": {
        "en": "Knockout stage — brilliant if you like stress, nerves, and grown adults treating a penalty like a tax audit. Someone goes through, someone goes home to explain a 0-0 to their family. I'd be useless in extra time — too tall for the wall, too awkward for the dance. Still, magic happens.",
        "nl": "Knock-outfase — geweldig als je van stress, zenuwen en volwassenen houdt die een penalty behandelen als een belastingcontrole. Iemand gaat door, iemand gaat naar huis om een 0-0 uit te leggen aan familie. Ik zou nutteloos zijn in verlenging — te lang voor de muur, te onhandig voor de dans. Toch gebeurt er magie.",
        "pt": "Fase eliminatória — ótimo se você curte estresse, nervos e adultos tratando um pênalti como auditoria fiscal. Alguém passa, alguém vai pra casa explicar um 0 a 0 pra família. Eu seria inútil na prorrogação — alto demais pra barreira, desajeitado demais pro passinho. Mesmo assim, acontece mágica.",
        "de": "K.o.-Phase — großartig, wenn man Stress, Nerven und Erwachsene mag, die einen Elfmeter wie eine Steuerprüfung behandeln. Einer kommt weiter, einer erklärt zu Hause ein 0:0 der Familie. Ich wäre in der Verlängerung nutzlos — zu groß für die Mauer, zu ungeschickt für den Tanz. Trotzdem passiert Magie.",
    },
    "joaquin": {
        "en": "The knockout rounds arrive like a flamenco call — one mistake and the guitar stops smiling. This is not survival football; this is art under thunder. When the ball asks for courage, answer with joy. The crowd does not want fear — it wants cante, sweat, and a story worth humming tomorrow.",
        "nl": "De knock-outronde arriveert als een flamenco-roep — één fout en de gitaar lacht niet meer. Dit is geen overlevingsvoetbal; dit is kunst onder donder. Als de bal moed vraagt, antwoord met vreugde. Het publiek wil geen angst — het wil cante, zweet en een verhaal dat je morgen neuriet.",
        "pt": "As eliminatórias chegam como um grito de flamenco — um erro e a guitarra para de sorrir. Isso não é futebol de sobrevivência; é arte sob trovão. Quando a bola pede coragem, responda com alegria. A torcida não quer medo — quer cante, suor e uma história pra cantarolar amanhã.",
        "de": "Die K.o.-Runde kommt wie ein Flamenco-Ruf — ein Fehler und die Gitarre hört auf zu lächeln. Das ist kein Überlebensfußball; das ist Kunst unter Donner. Wenn der Ball Mut verlangt, antworte mit Freude. Die Menge will keine Angst — sie will Cante, Schweiß und eine Geschichte zum Summen morgen.",
    },
}

MATCH_UPDATES = {
    11: {
        "style": "balotelli",
        "en": "Switzerland versus Canada at BC Place — two polite countries in a city famous for being polite. Perfect. I will not pretend this is fireworks; I will pretend I do not care, then care too much when someone misses an open goal. Why always the open goal? Because football enjoys drama more than I do.",
        "nl": "Zwitserland tegen Canada in BC Place — twee beleefde landen in een stad die beroemd is om beleefdheid. Perfect. Ik doe alsof dit geen vuurwerk is; ik doe alsof het me niets kan schelen, en dan scheelt het me te veel als iemand een open goal mist. Waarom altijd de open goal? Omdat voetbal van drama houdt — meer dan ik.",
        "pt": "Suíça contra Canadá no BC Place — dois países educados numa cidade famosa por educação. Perfeito. Vou fingir que não é fogos de artifício; vou fingir que não ligo, e depois ligo demais quando alguém perde gol feito. Por que sempre o gol feito? Porque o futebol gosta de drama mais do que eu.",
        "de": "Schweiz gegen Kanada im BC Place — zwei höfliche Länder in einer Stadt, die für Höflichkeit berühmt ist. Perfekt. Ich tue so, als wäre das kein Feuerwerk; ich tue so, als wäre es mir egal, und dann ist es mir zu viel, wenn jemand einen klaren Treffer vergibt. Warum immer der klare Treffer? Weil Fußball Drama liebt — mehr als ich.",
    },
    15: {
        "style": "kahn",
        "en": "Scotland against Morocco at Gillette — cold wind, old warriors, and a goalkeeper's mindset in every duel. The Atlas Lions roar; the Scots answer with stubborn chests. I want noise, discipline, and zero surrender in the six-yard box. In knockout terms this is already a semi-final for pride.",
        "nl": "Schotland tegen Marokko in Gillette — koude wind, oude strijders, en een keepersmentaliteit in elk duel. De Atlasleeuwen brullen; de Schotten antwoorden met koppige borsten. Ik wil lawaai, discipline en nul opgave in het zestienmetergebied. In knock-outtermen is dit al een halve finale voor trots.",
        "pt": "Escócia contra Marrocos em Gillette — vento frio, guerreiros antigos e mentalidade de goleiro em cada duelo. Os Leões do Atlas rugem; os escoceses respondem com peito teimoso. Quero barulho, disciplina e zero rendição na pequena área. Em termos eliminatórios, isso já é semifinal de orgulho.",
        "de": "Schottland gegen Marokko in Gillette — kalter Wind, alte Krieger und Torwart-Denken in jedem Zweikampf. Die Atlaslöwen brüllen; die Schotten antworten mit störrischen Brüsten. Ich will Lärm, Disziplin und null Aufgeben im Sechzehn. In K.o.-Begriffen ist das schon ein Halbfinale für den Stolz.",
    },
    17: {
        "style": "kahn",
        "en": "Scotland versus Brazil in Miami — Hard Rock heat and a samba hurricane against tartan stubbornness. The Scots will run until lungs burn; Brazil will play until the night applauds. Command your line, scream your orders, accept no softness. This is not a friendly. This is a trial by fire under palm trees.",
        "nl": "Schotland tegen Brazilië in Miami — Hard Rock-hitte en een sambahurricane tegen Schots koppigheid. De Schotten rennen tot de longen branden; Brazilië speelt tot de nacht applaudisseert. Leid je linie, brul je bevelen, accepteer geen zachtheid. Dit is geen oefenwedstrijd. Dit is vuurproef onder palmbomen.",
        "pt": "Escócia contra Brasil em Miami — calor do Hard Rock e furacão de samba contra teimosia de tartan. Os escoceses correm até faltar ar; o Brasil joga até a noite aplaudir. Comande sua linha, grite suas ordens, não aceite moleza. Isso não é amistoso. É julgamento de fogo sob palmeiras.",
        "de": "Schottland gegen Brasilien in Miami — Hard-Rock-Hitze und Samba-Hurrikan gegen schottische Sturheit. Die Schotten rennen, bis die Lungen brennen; Brasilien spielt, bis die Nacht applaudiert. Führt eure Linie, brüllt eure Befehle, akzeptiert keine Weichheit. Das ist kein Freundschaftsspiel. Das ist Feuerprobe unter Palmen.",
    },
    21: {
        "style": "gascoigne",
        "en": "Türkiye against Paraguay at Levi's Stadium — two nations who wear passion like a second skin. Turkish drums in the stands, Paraguayan harps in the soul, and somewhere between them a kid's dream still alive. Play with your heart first, tactics second. Football is feeling tonight, not homework.",
        "nl": "Türkiye tegen Paraguay in Levi's Stadium — twee naties die passie dragen als tweede huid. Turkse trommels op de tribune, Paraguayaanse harpen in de ziel, en ergens daartussen een droom die nog leeft. Speel eerst met je hart, tactiek daarna. Voetbal is vanavond voelen, geen huiswerk.",
        "pt": "Türkiye contra Paraguai no Levi's Stadium — duas nações que vestem paixão como segunda pele. Tambores turcos na arquibancada, harpas paraguaias na alma, e no meio disso um sonho de criança ainda vivo. Jogue com o coração primeiro, tática depois. Hoje o futebol é sentimento, não lição de casa.",
        "de": "Türkiye gegen Paraguay im Levi's Stadium — zwei Nationen, die Leidenschaft wie eine zweite Haut tragen. Türkische Trommeln auf den Rängen, paraguayische Harfen in der Seele, und dazwischen ein Kindheitstraum, der noch lebt. Spielt zuerst mit dem Herzen, Taktik danach. Heute ist Fußball Gefühl, keine Hausaufgabe.",
    },
    36: {
        "style": "gascoigne",
        "en": "Japan versus Sweden at Arrowhead — disciplined hearts against Viking calm in the loudest yard in America. Japan will sweep every loose cup in the stands; Sweden will sweep every doubt on the pitch. I want honesty, rhythm, and one moment so pure the crowd forgets to check the scoreboard.",
        "nl": "Japan tegen Zweden in Arrowhead — gedisciplineerde harten tegen Vikingen-kalmte in de luidste tuin van Amerika. Japan ruimt elk bekertje op de tribune op; Zweden ruimt elke twijfel op het veld op. Ik wil eerlijkheid, ritme en één moment zo puur dat het publiek vergeet het scorebord te checken.",
        "pt": "Japão contra Suécia no Arrowhead — corações disciplinados contra calma viking no pátio mais barulhento da América. O Japão varre cada copo na arquibancada; a Suécia varre cada dúvida no campo. Quero honestidade, ritmo e um momento tão puro que a torcida esqueça o placar.",
        "de": "Japan gegen Schweden im Arrowhead — disziplinierte Herzen gegen Wikinger-Ruhe im lautesten Hof Amerikas. Japan fegt jeden Becher auf den Rängen weg; Schweden fegt jeden Zweifel auf dem Platz weg. Ich will Ehrlichkeit, Rhythmus und einen Moment so rein, dass die Menge vergisst, auf die Anzeigetafel zu schauen.",
    },
    39: {
        "style": "crouch",
        "en": "Belgium versus Iran at SoFi — chocolate finesse meets Persian fire under a roof that looks like a spaceship. Belgium's golden generation is now more vintage than gold; Iran plays like losing is illegal. I'm 6'7\" and even I feel small when this intensity starts. Someone's robot dance will be off-beat tonight.",
        "nl": "België tegen Iran in SoFi — chocolade-finesse ontmoet Perzisch vuur onder een dak dat op een ruimteschip lijkt. Belgiës gouden generatie is nu meer vintage dan goud; Iran speelt alsof verliezen verboden is. Ik ben 1,95 m en zelfs ik voel me klein als deze intensiteit begint. Iemands robotdans valt vanavond uit de maat.",
        "pt": "Bélgica contra Irã no SoFi — finesse de chocolate encontra fogo persa sob um teto que parece nave espacial. A geração dourada da Bélgica agora é mais vintage que ouro; o Irã joga como se perder fosse crime. Tenho 2,02 m e até eu me sinto pequeno quando essa intensidade começa. O passinho robô de alguém vai sair fora do ritmo hoje.",
        "de": "Belgien gegen Iran im SoFi — Schokoladen-Finesse trifft persisches Feuer unter einem Dach wie ein Raumschiff. Belgiens goldene Generation ist jetzt eher Vintage als Gold; Iran spielt, als wäre Verlieren verboten. Ich bin 2,01 m und selbst ich fühle mich klein, wenn diese Intensität beginnt. Irgendwessen Robotertanz wird heute falsch sein.",
    },
    51: {
        "style": "joaquin",
        "en": "France versus Iraq at Lincoln Financial Field — tricolour silk against Mesopotamian lions in Philadelphia brick and noise. Mbappé may paint speed; Iraq paints courage with fewer colours but deeper ink. This is not a spreadsheet match. This is cante under floodlights — art versus hunger, and hunger sings loud.",
        "nl": "Frankrijk tegen Irak op Lincoln Financial Field — tricolore zijde tegen mesopotamische leeuwen in Philadelphia-baksteen en lawaai. Mbappé schildert snelheid; Irak schildert moed met minder kleuren maar diepere inkt. Dit is geen spreadsheet-wedstrijd. Dit is cante onder lichtmasten — kunst tegen honger, en honger zingt luid.",
        "pt": "França contra Iraque no Lincoln Financial Field — seda tricolor contra leões mesopotâmicos em tijolo e barulho de Philadelphia. Mbappé pinta velocidade; o Iraque pinta coragem com menos cores e tinta mais funda. Não é jogo de planilha. É cante sob holofote — arte contra fome, e a fome canta alto.",
        "de": "Frankreich gegen Irak im Lincoln Financial Field — Trikolore-Seide gegen mesopotamische Löwen in Philadelphia-Ziegel und Lärm. Mbappé malt Geschwindigkeit; der Irak malt Mut mit weniger Farben, aber tieferer Tinte. Das ist kein Tabellen-Spiel. Das ist Cante unter Flutlicht — Kunst gegen Hunger, und Hunger singt laut.",
    },
    53: {
        "style": "joaquin",
        "en": "Norway versus France at Gillette — Haaland's hammer against Mbappé's lightning, Viking thunder against Parisian grace. Two prices of war, one ball, zero room for fear. When giants collide, the grass becomes a stage. Play it like Betis on a Sunday: joy first, result second, heart always.",
        "nl": "Noorwegen tegen Frankrijk in Gillette — Haalands hamer tegen Mbappé's bliksem, Vikingendonder tegen Parijse gratie. Twee oorlogsprijzen, één bal, nul ruimte voor angst. Als reuzen botsen, wordt het gras een podium. Speel het als Betis op zondag: vreugde eerst, resultaat daarna, hart altijd.",
        "pt": "Noruega contra França em Gillette — o martelo de Haaland contra o raio de Mbappé, trovão viking contra graça parisiense. Dois preços de guerra, uma bola, zero espaço pro medo. Quando gigantes colidem, o gramado vira palco. Jogue como o Betis no domingo: alegria primeiro, resultado depois, coração sempre.",
        "de": "Norwegen gegen Frankreich in Gillette — Haalands Hammer gegen Mbappés Blitz, Wikinger-Donner gegen Pariser Anmut. Zwei Kriegspreise, ein Ball, null Raum für Angst. Wenn Giganten kollidieren, wird der Rasen zur Bühne. Spielt es wie Betis am Sonntag: Freude zuerst, Ergebnis danach, Herz immer.",
    },
    54: {
        "style": "balotelli",
        "en": "Senegal versus Iraq at BMO Field — Teranga sunshine against Mesopotamian fire in Toronto's compact theatre. Everyone expects noise; I expect someone to do something stupid and brilliant in the same minute. That is football. That is me. Why always the same minute? Because fate has humour.",
        "nl": "Senegal tegen Irak op BMO Field — Teranga-zon tegen mesopotamisch vuur in Toronto's compacte theater. Iedereen verwacht lawaai; ik verwacht dat iemand in dezelfde minuut iets doms én briljants doet. Dat is voetbal. Dat ben ik. Waarom altijd dezelfde minuut? Omdat het lot humor heeft.",
        "pt": "Senegal contra Iraque no BMO Field — sol da Teranga contra fogo mesopotâmico no teatro compacto de Toronto. Todos esperam barulho; eu espero alguém fazer algo idiota e brilhante no mesmo minuto. Isso é futebol. Isso sou eu. Por que sempre o mesmo minuto? Porque o destino tem humor.",
        "de": "Senegal gegen Irak im BMO Field — Teranga-Sonne gegen mesopotamisches Feuer in Torontos kompaktem Theater. Alle erwarten Lärm; ich erwarte, dass jemand in derselben Minute etwas Dummes und Brillantes tut. Das ist Fußball. Das bin ich. Warum immer dieselbe Minute? Weil das Schicksal Humor hat.",
    },
    66: {
        "style": "crouch",
        "en": "DR Congo versus Uzbekistan at Mercedes-Benz Stadium — Leopards against White Wolves in Atlanta humidity. On paper it looks like a nature documentary; on grass it is elbows, rhythm, and one header I might actually win. If not, there is always the robot celebration for moral victory.",
        "nl": "DR Congo tegen Oezbekistan in Mercedes-Benz Stadium — Luipaarden tegen Witte Wolven in Atlantische vochtigheid. Op papier lijkt het een natuurdocumentaire; op gras zijn het ellebogen, ritme en één kopbal die ik misschien wél win. Zo niet, dan is er altijd nog de robotviering als morele overwinning.",
        "pt": "RD Congo contra Uzbequistão no Mercedes-Benz Stadium — Leopardos contra Lobos Brancos na umidade de Atlanta. No papel parece documentário de natureza; no gramado são cotovelos, ritmo e uma cabeçada que eu talvez ganhe. Se não, ainda tem a comemoração robô como vitória moral.",
        "de": "DR Kongo gegen Usbekistan im Mercedes-Benz Stadium — Leoparden gegen Weiße Wölfe in Atlantas Feuchtigkeit. Auf dem Papier wirkt es wie eine Naturdoku; auf dem Rasen sind es Ellbogen, Rhythmus und ein Kopfball, den ich vielleicht gewinne. Wenn nicht, bleibt die Roboter-Feier als moralischer Sieg.",
    },
    70: {
        "style": "gascoigne",
        "en": "Panama versus Croatia at BMO Field — Canal Boys against checkered kings, tears of joy against tears of almost. Modrić still conducts the ball like a sad beautiful song; Panama still runs like the first time they qualified. I want one moment raw enough to make strangers hug. That is the Geordie in me.",
        "nl": "Panama tegen Kroatië op BMO Field — Kanaaljongens tegen geblokte koningen, tranen van vreugde tegen tranen van bijna. Modrić dirigeert de bal nog als een mooi verdrietig lied; Panama rent nog als bij de eerste kwalificatie. Ik wil één moment zo rauw dat vreemden elkaar omhelzen. Dat is de Geordie in mij.",
        "pt": "Panamá contra Croácia no BMO Field — Garotos do Canal contra reis xadrez, lágrimas de alegria contra lágrimas de quase. Modrić ainda conduz a bola como canção linda e triste; o Panamá ainda corre como na primeira classificação. Quero um momento cru o bastante pra estranhos se abraçarem. Isso é o Geordie em mim.",
        "de": "Panama gegen Kroatien im BMO Field — Kanal-Jungs gegen karierte Könige, Freudentränen gegen Fast-Tränen. Modrić dirigiert den Ball noch wie ein schönes trauriges Lied; Panama rennt noch wie bei der ersten Qualifikation. Ich will einen Moment so roh, dass Fremde sich umarmen. Das ist der Geordie in mir.",
    },
    82: {
        "style": "joaquin",
        "en": "Levi's Stadium, Santa Clara — Silicon Valley steel and knockout breath between tech campuses. The 49ers taught this turf to love drama; tonight football adds flamenco heartbeat to NFL ghosts. When the lights cut the valley dark, only courage and touch survive. Play beautiful. Play brave. Play like the ball is singing.",
        "nl": "Levi's Stadium, Santa Clara — Silicon Valley-staal en knock-outadem tussen techcampussen. De 49ers leerden dit veld drama liefhebben; vanavond voegt voetbal flamenco-hartslag toe aan NFL-geesten. Als de lichten de vallei donker snijden, overleven alleen moed en gevoel. Speel mooi. Speel braf. Speel alsof de bal zingt.",
        "pt": "Levi's Stadium, Santa Clara — aço do Vale do Silício e respiração eliminatória entre campi de tecnologia. Os 49ers ensinaram esse gramado a amar drama; hoje o futebol acrescenta batida flamenca aos fantasmas da NFL. Quando as luzes cortam o vale no escuro, só coragem e toque sobrevivem. Jogue bonito. Jogue valente. Jogue como se a bola cantasse.",
        "de": "Levi's Stadium, Santa Clara — Silicon-Valley-Stahl und K.o.-Atem zwischen Tech-Campus. Die 49ers lehrten diesen Rasen Drama lieben; heute fügt Fußball Flamenco-Puls zu NFL-Geistern hinzu. Wenn die Lichter das Tal dunkel schneiden, überleben nur Mut und Gefühl. Spielt schön. Spielt mutig. Spielt, als würde der Ball singen.",
    },
    84: {
        "style": "balotelli",
        "en": "BMO Field, Toronto — the smallest knockout room on the map and therefore the loudest for mistakes. MLS nights made this grass familiar; World Cup nights make it unforgiving. You cannot hide in a stadium this intimate. I like that. Pressure reveals who is real and who is only pretending on Instagram.",
        "nl": "BMO Field, Toronto — de kleinste knock-outruimte op de kaart en daardoor het luidst voor fouten. MLS-avonden maakten dit gras vertrouwd; WK-avonden maken het genadeloos. Je kunt je niet verstoppen in een stadion zo intiem. Dat vind ik mooi. Druk toont wie echt is en wie alleen op Instagram doet alsof.",
        "pt": "BMO Field, Toronto — a menor sala eliminatória do mapa e, por isso, a mais barulhenta pros erros. Noites de MLS deixaram esse gramado familiar; noites de Copa o tornam implacável. Não dá pra se esconder num estádio tão íntimo. Eu gosto disso. Pressão mostra quem é real e quem só finge no Instagram.",
        "de": "BMO Field, Toronto — der kleinste K.o.-Raum auf der Karte und deshalb der lauteste für Fehler. MLS-Nächte machten diesen Rasen vertraut; WM-Nächte machen ihn gnadenlos. In einem so intimen Stadion kann man sich nicht verstecken. Das mag ich. Druck zeigt, wer echt ist und wer nur auf Instagram so tut.",
    },
    101: {
        "style": "kahn",
        "en": "AT&T Stadium — a World Cup semi-final beneath a screen big enough to expose every heartbeat. There is no tomorrow in this building, only command, roar, and the cruel mathematics of ninety minutes. Two nations enter; one reaches the final. Stand tall. Organise. Punish fear. The mirror does not forgive softness.",
        "nl": "AT&T Stadium — een WK-halve finale onder een scherm groot genoeg om elke hartslag bloot te leggen. In dit gebouw is er geen morgen, alleen bevel, gebrul en de wrede wiskunde van negentig minuten. Twee naties gaan naar binnen; één bereikt de finale. Sta recht. Organiseer. Straaf angst. De spiegel vergeeft geen zachtheid.",
        "pt": "AT&T Stadium — uma semifinal de Copa sob uma tela grande o bastante pra expor cada batida do coração. Não há amanhã neste prédio, só comando, rugido e a matemática cruel de noventa minutos. Duas nações entram; uma chega à final. Fique ereto. Organize. Puna o medo. O espelho não perdoa moleza.",
        "de": "AT&T Stadium — ein WM-Halbfinale unter einer Leinwand groß genug, jeden Herzschlag zu entblößen. In diesem Gebäude gibt es kein Morgen, nur Befehl, Brüllen und die grausame Mathematik von neunzig Minuten. Zwei Nationen gehen hinein; eine erreicht das Finale. Steht aufrecht. Organisiert. Bestraft Angst. Der Spiegel verzeiht keine Weichheit.",
    },
}


def apply_analyst_updates(match_comments: dict, knockout_comments: dict) -> None:
    for mn, entry in MATCH_UPDATES.items():
        if mn in match_comments:
            match_comments[mn] = entry
        elif mn in knockout_comments:
            knockout_comments[mn] = entry
