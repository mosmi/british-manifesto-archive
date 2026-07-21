/* ============================================================
   THE BRITISH MANIFESTO ARCHIVE — Data
   ============================================================ */

const PARTIES = {
  /* ── Primary Westminster parties ─────────────────────────── */
  labour: {
    id: 'labour', name: 'The Labour Party', shortName: 'Labour',
    color: '#E4003B', dim: 'rgba(228,0,59,0.16)',
    founded: 1900, spectrum: 'Centre-left / Left', isPrimary: true,
    nation: 'england',
    description: 'Founded in 1900 by trade unions and socialist societies, the Labour Party has been the principal party of the British left throughout the twentieth and twenty-first centuries. It formed its first government in 1924 under Ramsay MacDonald, and achieved a landmark majority in 1945 under Clement Attlee, whose administration created the National Health Service and the modern welfare state. After years of opposition through the Thatcher and Major era, Tony Blair\'s "New Labour" won a historic landslide in 1997, reshaping the centre-left for a generation. The party returned to government in 2024 under Keir Starmer with a second historic majority.',
  },
  conservative: {
    id: 'conservative', name: 'Conservative and Unionist Party', shortName: 'Conservatives',
    color: '#0087DC', dim: 'rgba(0,135,220,0.16)',
    founded: 1834, spectrum: 'Centre-right / Right', isPrimary: true,
    nation: 'england',
    description: 'One of the two oldest and most successful parties in British democratic history, the Conservatives—also known as the Tories—have dominated twentieth-century British politics, governing for more than half the years since 1945. The party\'s postwar leaders include Winston Churchill, Anthony Eden, Harold Macmillan, Edward Heath, Margaret Thatcher (1979–1990), and John Major. The Thatcher governments of 1979–1990 represented a defining ideological turn toward free-market economics that reshaped British society. After thirteen years of Labour government, David Cameron returned the party to power in 2010.',
  },
  libdem: {
    id: 'libdem', name: 'Liberal Democrats', shortName: 'Liberal Democrats',
    color: '#FAA61A', dim: 'rgba(250,166,26,0.16)',
    founded: 1988, spectrum: 'Centre / Centre-left', isPrimary: true,
    nation: 'england',
    description: 'The Liberal Democrats were formed in 1988 from the merger of the Liberal Party and the Social Democratic Party. The Liberals themselves trace their origins to the Whig tradition and were one of the two dominant parties until Labour\'s rise in the early twentieth century. The Liberal Democrats became the third-largest party in Westminster, achieving their best postwar result of 62 seats in 2005 under Charles Kennedy. In 2010, under Nick Clegg, the party entered into a formal Coalition Government with the Conservatives—the first peacetime coalition since the 1930s. This proved electorally catastrophic and the party was reduced to just 8 seats in 2015. Under Ed Davey, the party achieved 72 seats in the 2024 election.',
  },
  green: {
    id: 'green', name: 'Green Party of England and Wales', shortName: 'Green Party',
    color: '#00B140', dim: 'rgba(0,177,64,0.14)',
    founded: 1975, spectrum: 'Left / Green', isPrimary: false,
    nation: 'england',
    description: 'The Ecology Party (1975–85), itself the successor to PEOPLE (founded 1973), was renamed the Green Party in 1985; the Green Party of England and Wales took its present form in 1990 when the Scottish and Northern Ireland parties became separate organisations. The party focuses on environmental policy, social justice, and opposition to austerity. It won its first Westminster seat in 2010 (Brighton Pavilion, Caroline Lucas) and increased its representation to 4 seats in 2024.',
  },
  ukip: {
    id: 'ukip', name: 'UK Independence Party', shortName: 'UKIP',
    color: '#70147A', dim: 'rgba(112,20,122,0.14)',
    founded: 1993, spectrum: 'Right / Eurosceptic', isPrimary: false,
    nation: 'england',
    description: 'UKIP rose to prominence in the 2010s as a Eurosceptic, right-wing populist party under Nigel Farage. Despite winning nearly 4 million votes in 2015 (12.6% of the vote), the party\'s first-past-the-post disadvantage left it with only one MP. The party largely collapsed after the 2016 Brexit referendum it had helped to bring about.',
  },
  reform: {
    id: 'reform', name: 'Reform UK', shortName: 'Reform UK',
    color: '#12B6CF', dim: 'rgba(18,182,207,0.14)',
    founded: 2018, spectrum: 'Right / National-populist', isPrimary: false,
    nation: 'england',
    description: 'Reform UK, originally the Brexit Party, was relaunched under Nigel Farage in 2021. In the 2024 election the party won 5 seats but achieved 14.3% of the national vote, making it the third-largest party by popular support, though not by seats.',
  },

  /* ── Wales ───────────────────────────────────────────────── */
  plaid: {
    id: 'plaid', name: 'Plaid Cymru', shortName: 'Plaid Cymru',
    color: '#008672', dim: 'rgba(0,134,114,0.14)',
    founded: 1925, spectrum: 'Centre-left / Welsh Nationalist', isPrimary: false,
    nation: 'wales',
    description: 'Plaid Cymru (Party of Wales) campaigns for Welsh independence and has been a consistent presence in Welsh politics since winning its first Westminster seat in 1966. The party typically holds 3–4 Westminster seats and has been the second-largest party in the Senedd Cymru.',
  },
  welshlab: {
    id: 'welshlab', name: 'Welsh Labour', shortName: 'Welsh Labour',
    color: '#E4003B', dim: 'rgba(228,0,59,0.16)',
    founded: 1900, spectrum: 'Centre-left', isPrimary: false,
    nation: 'wales',
    description: 'Welsh Labour is the devolved organisation of the Labour Party in Wales. It has been the largest party in the Senedd Cymru (Welsh Parliament) at every election since the institution\'s establishment in 1999, though it has never won an outright majority. Welsh Labour has governed Wales continuously, sometimes in coalition or with external support.',
  },
  welshcon: {
    id: 'welshcon', name: 'Welsh Conservatives', shortName: 'Welsh Conservatives',
    color: '#0087DC', dim: 'rgba(0,135,220,0.16)',
    founded: 1834, spectrum: 'Centre-right', isPrimary: false,
    nation: 'wales',
    description: 'The Welsh Conservatives are the Welsh branch of the Conservative Party. They have been the principal opposition to Labour in the Senedd, replacing Plaid Cymru as the second-largest party in 2021 with 16 seats.',
  },
  welshlibdem: {
    id: 'welshlibdem', name: 'Welsh Liberal Democrats', shortName: 'Welsh Liberal Democrats',
    color: '#FAA61A', dim: 'rgba(250,166,26,0.16)',
    founded: 1988, spectrum: 'Centre', isPrimary: false,
    nation: 'wales',
    description: 'The Welsh Liberal Democrats contest both Senedd and Westminster elections in Wales. The party held 3 Senedd seats between 1999 and 2011, declining thereafter.',
  },
  walesgrn: {
    id: 'walesgrn', name: 'Wales Green Party', shortName: 'Wales Green Party',
    color: '#00B140', dim: 'rgba(0,177,64,0.14)',
    founded: 1990, spectrum: 'Left / Green', isPrimary: false,
    nation: 'wales',
    description: 'The Wales Green Party is part of the Green Party of England and Wales, contesting elections across Wales.',
  },
  gwlad: {
    id: 'gwlad', name: 'Gwlad', shortName: 'Gwlad',
    color: '#1B4D3E', dim: 'rgba(27,77,62,0.14)',
    founded: 2018, spectrum: 'Centre / Welsh nationalist', isPrimary: false,
    nation: 'wales',
    description: 'Gwlad is a Welsh nationalist party advocating independence and economic reform. It has contested Senedd elections since 2021.',
  },
  propel: {
    id: 'propel', name: 'Propel', shortName: 'Propel',
    color: '#5B2C6F', dim: 'rgba(91,44,111,0.14)',
    founded: 2020, spectrum: 'Centre / Welsh nationalist', isPrimary: false,
    nation: 'wales',
    description: 'Propel is a Welsh nationalist party that contested Senedd elections in 2021 and 2026.',
  },
  abolish: {
    id: 'abolish', name: 'Abolish the Welsh Assembly Party', shortName: 'Abolish',
    color: '#B91C1C', dim: 'rgba(185,28,28,0.14)',
    founded: 2020, spectrum: 'Right / Anti-devolution', isPrimary: false,
    nation: 'wales',
    description: 'The Abolish the Welsh Assembly Party campaigned to abolish the Senedd. It contested the 2021 election.',
  },
  heritage: {
    id: 'heritage', name: 'Heritage Party', shortName: 'Heritage',
    color: '#7C2D12', dim: 'rgba(124,45,18,0.14)',
    founded: 2020, spectrum: 'Right / Social conservative', isPrimary: false,
    nation: 'wales',
    description: 'The Heritage Party contested the 2026 Senedd election on a socially conservative platform.',
  },

  /* ── Scotland ────────────────────────────────────────────── */
  snp: {
    id: 'snp', name: 'Scottish National Party', shortName: 'SNP',
    color: '#FDF38E', dim: 'rgba(253,243,142,0.14)',
    founded: 1934, spectrum: 'Centre-left', isPrimary: false,
    nation: 'scotland',
    description: 'The SNP won its first Westminster seat at a general election in 1970. The May 2015 election was its best performance: 50% of the Scottish vote and 56 seats. In 2019, the SNP won 48 seats and 45% of the Scottish vote. The party has governed Scotland through the Scottish Parliament since 2007 and campaigns for Scottish independence.',
  },
  scottishlab: {
    id: 'scottishlab', name: 'Scottish Labour', shortName: 'Scottish Labour',
    color: '#E4003B', dim: 'rgba(228,0,59,0.16)',
    founded: 1900, spectrum: 'Centre-left', isPrimary: false,
    nation: 'scotland',
    description: 'Scottish Labour is the Scottish branch of the Labour Party. It was the dominant force in Scottish politics for much of the twentieth century and won the most seats in the first two Scottish Parliament elections (1999, 2003), governing in coalition with the Liberal Democrats. The SNP replaced Labour as the largest party in 2007. Scottish Labour lost 40 of its 41 Westminster seats in the 2015 general election.',
  },
  scottishcon: {
    id: 'scottishcon', name: 'Scottish Conservatives', shortName: 'Scottish Conservatives',
    color: '#0087DC', dim: 'rgba(0,135,220,0.16)',
    founded: 1834, spectrum: 'Centre-right', isPrimary: false,
    nation: 'scotland',
    description: 'The Scottish Conservatives became the second-largest party at Holyrood in 2016 under Ruth Davidson, winning 31 MSPs. They have been the principal pro-union opposition to the SNP at Holyrood.',
  },
  scottishlibdem: {
    id: 'scottishlibdem', name: 'Scottish Liberal Democrats', shortName: 'Scottish Liberal Democrats',
    color: '#FAA61A', dim: 'rgba(250,166,26,0.16)',
    founded: 1988, spectrum: 'Centre', isPrimary: false,
    nation: 'scotland',
    description: 'The Scottish Liberal Democrats governed Scotland in coalition with Labour from 1999 to 2007. They retain a small presence at Holyrood and several Westminster seats in rural Scotland.',
  },
  scottishgrn: {
    id: 'scottishgrn', name: 'Scottish Green Party', shortName: 'Scottish Greens',
    color: '#00B140', dim: 'rgba(0,177,64,0.14)',
    founded: 1990, spectrum: 'Left / Green', isPrimary: false,
    nation: 'scotland',
    description: 'The Scottish Greens contest Scottish Parliament elections and have grown significantly, winning 7 regional MSPs in 2003 and 7 again in 2021. The party entered into a formal co-operation agreement with the SNP government at Holyrood in 2021.',
  },
  alba: {
    id: 'alba', name: 'Alba Party', shortName: 'Alba',
    color: '#005EB8', dim: 'rgba(0,94,184,0.14)',
    founded: 2021, spectrum: 'Left / Scottish independence', isPrimary: false,
    nation: 'scotland',
    description: 'The Alba Party was founded in 2021 by former First Minister Alex Salmond after he left the SNP. It contested the 2021 Scottish Parliament election on a pro-independence platform and the 2024 UK general election in Scotland. Its 2024 Westminster manifesto, “Yes to Scottish Independence”, is held in this archive.',
  },
  solidarity: {
    id: 'solidarity', name: 'Solidarity', shortName: 'Solidarity',
    color: '#CC0000', dim: 'rgba(204,0,0,0.14)',
    founded: 2006, spectrum: 'Left / Scottish socialist', isPrimary: false,
    nation: 'scotland',
    description: 'Solidarity was a left-wing Scottish socialist party founded in 2006 after a split from the Scottish Socialist Party. It contested the 2007 Scottish Parliament election and was associated with Tommy Sheridan.',
  },
  rise: {
    id: 'rise', name: 'RISE', shortName: 'RISE',
    color: '#E30613', dim: 'rgba(227,6,19,0.14)',
    founded: 2015, spectrum: 'Left / Scottish socialist', isPrimary: false,
    nation: 'scotland',
    description: 'RISE (Respect, Independence, Socialism and Environmentalism) was a left-wing electoral alliance that contested the 2016 Scottish Parliament election.',
  },
  allforunity: {
    id: 'allforunity', name: 'All for Unity', shortName: 'All for Unity',
    color: '#1D4ED8', dim: 'rgba(29,78,216,0.14)',
    founded: 2021, spectrum: 'Centre / Pro-union', isPrimary: false,
    nation: 'scotland',
    description: 'All for Unity was a pro-union electoral alliance that contested the 2021 Scottish Parliament election, urging tactical voting against the SNP and Scottish Greens.',
  },
  isp: {
    id: 'isp', name: 'Independence for Scotland Party', shortName: 'ISP',
    color: '#2E8B57', dim: 'rgba(46,139,87,0.14)',
    founded: 2020, spectrum: 'Centre-left / Scottish independence', isPrimary: false,
    nation: 'scotland',
    description: 'The Independence for Scotland Party (ISP) was founded in 2020 as a pro-independence party advocating a dual-mandate strategy at Holyrood. It has contested Scottish Parliament elections since 2021.',
  },
  scottishfamily: {
    id: 'scottishfamily', name: 'Scottish Family Party', shortName: 'Scottish Family',
    color: '#7C3AED', dim: 'rgba(124,58,237,0.14)',
    founded: 2020, spectrum: 'Right / Social conservative', isPrimary: false,
    nation: 'scotland',
    description: 'The Scottish Family Party is a socially conservative party that contests Scottish Parliament elections on family-values and pro-life platforms.',
  },
  scottishlibertarian: {
    id: 'scottishlibertarian', name: 'Scottish Libertarian Party', shortName: 'Scottish Libertarian',
    color: '#F4C430', dim: 'rgba(244,196,48,0.14)',
    founded: 2012, spectrum: 'Libertarian', isPrimary: false,
    nation: 'scotland',
    description: 'The Scottish Libertarian Party advocates minimal government, free markets, and individual liberty. It contests Holyrood elections on the regional lists.',
  },
  sovereignty: {
    id: 'sovereignty', name: 'Sovereignty Scotland', shortName: 'Sovereignty Scotland',
    color: '#1B365D', dim: 'rgba(27,54,93,0.14)',
    founded: 2024, spectrum: 'Right / Scottish nationalist', isPrimary: false,
    nation: 'scotland',
    description: 'Sovereignty Scotland is a right-wing Scottish nationalist party that contested the 2026 Scottish Parliament election.',
  },
  scottishchristian: {
    id: 'scottishchristian', name: 'Scottish Christian Party', shortName: 'Scottish Christian',
    color: '#4B0082', dim: 'rgba(75,0,130,0.14)',
    founded: 2004, spectrum: 'Right / Christian', isPrimary: false,
    nation: 'scotland',
    description: 'The Scottish Christian Party contests elections in Scotland on a Christian social-conservative platform, including the 2007 Scottish Parliament election.',
  },

  /* ── Northern Ireland ────────────────────────────────────── */
  dup: {
    id: 'dup', name: 'Democratic Unionist Party', shortName: 'DUP',
    color: '#D46A4C', dim: 'rgba(212,106,76,0.14)',
    founded: 1971, spectrum: 'Right / Unionist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The DUP replaced the Ulster Unionist Party as the largest unionist party at Westminster in 2001 and at Stormont in 2003. Founded by Ian Paisley, the party played a key constitutional role in 2017–2019 when it supported the Conservative minority government through a Confidence and Supply Agreement worth £1 billion for Northern Ireland.',
  },
  sinnfein: {
    id: 'sinnfein', name: 'Sinn Féin', shortName: 'Sinn Féin',
    color: '#326760', dim: 'rgba(50,103,96,0.14)',
    founded: 1905, spectrum: 'Left / Irish Republican', isPrimary: false,
    nation: 'northern-ireland',
    description: 'Sinn Féin is an Irish republican, left-wing party operating on both sides of the Irish border. Its Westminster MPs follow an abstentionist policy and do not take their seats in the House of Commons. A nationalist party became the largest party in the Northern Ireland Assembly for the first time in 2022 when Sinn Féin won 27 seats.',
  },
  sdlp: {
    id: 'sdlp', name: 'Social Democratic & Labour Party', shortName: 'SDLP',
    color: '#2AA82C', dim: 'rgba(42,168,44,0.14)',
    founded: 1970, spectrum: 'Centre-left / Irish Nationalist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The SDLP is a moderate Irish nationalist and social-democratic party in Northern Ireland. Its MPs sit with the Labour Party at Westminster. The party was central to the Good Friday Agreement of 1998. In 2017, for the first time since its foundation, the SDLP failed to win any Westminster seats.',
  },
  alliance: {
    id: 'alliance', name: 'Alliance Party of Northern Ireland', shortName: 'Alliance',
    color: '#F6CB2F', dim: 'rgba(246,203,47,0.14)',
    founded: 1970, spectrum: 'Centre / Cross-community', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The Alliance Party is a cross-community, centrist party in Northern Ireland aligned with the Liberal Democrats at Westminster. The party won its first Westminster seat in 2019 and has grown significantly, winning 17 seats in the 2022 Northern Ireland Assembly elections — its best ever result.',
  },
  uup: {
    id: 'uup', name: 'Ulster Unionist Party', shortName: 'UUP',
    color: '#48A5EE', dim: 'rgba(72,165,238,0.16)',
    founded: 1905, spectrum: 'Centre-right / Unionist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The Ulster Unionist Party was the dominant force in Northern Ireland from partition in 1922 until the early 2000s. UUP MPs took the Conservative whip at Westminster until 1974, when Heath removed the whip after UUP opposition to the Sunningdale Agreement. The UUP was instrumental in negotiating the Good Friday Agreement of 1998. The DUP replaced it as the largest unionist party at Westminster from 2001.',
  },
  vanguard: {
    id: 'vanguard', name: 'Vanguard Unionist Progressive Party', shortName: 'Vanguard',
    color: '#5C4B8A', dim: 'rgba(92,75,138,0.16)',
    founded: 1972, spectrum: 'Right / Unionist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The Vanguard Unionist Progressive Party was founded by William Craig in 1972 as a hard-line unionist party opposing power-sharing with nationalists. It won three Westminster seats at the February 1974 general election before merging into the Ulster Unionist Party in 1978.',
  },
  gpni: {
    id: 'gpni', name: 'Green Party Northern Ireland', shortName: 'Green Party NI',
    color: '#8dc63f', dim: 'rgba(141,198,63,0.14)',
    founded: 1983, spectrum: 'Left / Green', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The Green Party in Northern Ireland is a separate organisation from the Green Party of England and Wales. It has won seats in the Northern Ireland Assembly and Belfast City Council.',
  },
  pup: {
    id: 'pup', name: 'Progressive Unionist Party', shortName: 'PUP',
    color: '#2B45A2', dim: 'rgba(43,69,162,0.14)',
    founded: 1979, spectrum: 'Left / Unionist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The Progressive Unionist Party is a small left-wing unionist party in Northern Ireland historically linked to the Ulster Volunteer Force. It won 2 Assembly seats in 1998 and 1 in 2003 and 2007.',
  },
  tuv: {
    id: 'tuv', name: 'Traditional Unionist Voice', shortName: 'TUV',
    color: '#0C3A6A', dim: 'rgba(12,58,106,0.14)',
    founded: 2007, spectrum: 'Right / Unionist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'Traditional Unionist Voice was founded in 2007 by Jim Allister MEP, who opposed the DUP\'s participation in power-sharing with Sinn Féin. The party opposes the Northern Ireland Protocol and the Windsor Framework.',
  },
  niwc: {
    id: 'niwc', name: "Northern Ireland Women's Coalition", shortName: "Women's Coalition",
    color: '#D45D79', dim: 'rgba(212,93,121,0.14)',
    founded: 1996, spectrum: 'Centre / Cross-community / Feminism', isPrimary: false,
    nation: 'northern-ireland',
    description: "The Northern Ireland Women's Coalition was a cross-community party active from 1996 to 2006. Founded by Monica McWilliams and Pearl Sagar, it sought to ensure women's representation in the peace talks and the Northern Ireland Assembly, where it held two seats from 1998 to 2003.",
  },
  pbp: {
    id: 'pbp', name: 'People Before Profit Alliance', shortName: 'People Before Profit',
    color: '#E91D24', dim: 'rgba(233,29,36,0.14)',
    founded: 2005, spectrum: 'Left / Socialist / Irish Republican', isPrimary: false,
    nation: 'northern-ireland',
    description: 'People Before Profit is a democratic socialist and republican party active in both the Republic of Ireland and Northern Ireland. It has won seats in the Northern Ireland Assembly, representing Belfast West and Foyle.',
  },
  sea: {
    id: 'sea', name: 'Socialist Environmental Alliance', shortName: 'Socialist Environmental Alliance',
    color: '#008080', dim: 'rgba(0,128,128,0.14)',
    founded: 2003, spectrum: 'Left / Ecosocialist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The Socialist Environmental Alliance was a small ecosocialist party in Northern Ireland formed in 2003, primarily active in Derry. It contested the 2003 and 2007 Assembly elections.',
  },
  rsf: {
    id: 'rsf', name: 'Republican Sinn Féin', shortName: 'Republican Sinn Féin',
    color: '#006600', dim: 'rgba(0,102,0,0.14)',
    founded: 1986, spectrum: 'Left / Irish Republican / Abstentionist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'Republican Sinn Féin was formed in 1986 following a split in Sinn Féin over the decision to end its policy of abstentionism from Dáil Éireann. It opposes the Good Friday Agreement.',
  },
  nicon: {
    id: 'nicon', name: 'Northern Ireland Conservatives', shortName: 'NI Conservatives',
    color: '#0087DC', dim: 'rgba(0,135,220,0.14)',
    founded: 1989, spectrum: 'Centre-right / Unionist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The Northern Ireland Conservatives are the regional branch of the UK Conservative Party. The party has stood candidates in both Westminster and devolved elections in Northern Ireland directly since 1989, campaigning on a centre-right, pro-Union platform.',
  },
  workerspartyie: {
    id: 'workerspartyie', name: "Workers' Party", shortName: "Workers' Party",
    color: '#D40000', dim: 'rgba(212,0,0,0.14)',
    founded: 1970, spectrum: 'Left / Democratic Socialist / Irish Republican', isPrimary: false,
    nation: 'northern-ireland',
    description: "The Workers' Party is a democratic socialist and Irish republican party active throughout Ireland. Historically emerging from the 1970 split in Sinn Féin (as Official Sinn Féin), the party was renamed the Workers' Party in 1982. It won seats in the 1982 Northern Ireland Assembly and Belfast City Council, and has contested modern Stormont elections across multiple constituencies.",
  },

  /* ── Other / fringe parties ──────────────────────────────── */
  commonwealth: {
    id: 'commonwealth', name: 'Common Wealth Party', shortName: 'Common Wealth',
    color: '#7A1F2E', dim: 'rgba(122,31,46,0.14)',
    founded: 1942, spectrum: 'Left / Common ownership', isPrimary: false,
    nation: 'others',
    description: 'The Common Wealth Party was founded in 1942 by Sir Richard Acland as a socialist party committed to common ownership and postwar reconstruction. It won its only Westminster seat at the 1945 general election when Ernest Millington took Chelmsford. The party declined rapidly afterwards and was dissolved later that year, with many members joining the Labour Party.',
  },
  spgb: {
    id: 'spgb', name: 'Socialist Party of Great Britain', shortName: 'SPGB',
    color: '#A61C30', dim: 'rgba(166,28,48,0.14)',
    founded: 1904, spectrum: 'Far-left / World socialism', isPrimary: false,
    nation: 'others',
    status: 'active',
    contests: ['westminster', 'london'],
    description: 'The Socialist Party of Great Britain (SPGB) was founded in 1904 as a breakaway from the Social Democratic Federation and is the oldest existing socialist party in Britain. An "impossibilist" party, it advocates world socialism established by a conscious democratic majority, refuses to campaign for reforms of capitalism, and famously makes no election promises. It has contested elections at every level without ever winning a seat, including the London County Council election of 1958, when it stood three candidates in East London.',
  },
  communist: {
    id: 'communist', name: 'Communist Party of Great Britain', shortName: 'CPGB',
    color: '#EF0000', dim: 'rgba(239,0,0,0.14)',
    founded: 1920, spectrum: 'Far-left / Communist', isPrimary: false,
    nation: 'others',
    status: 'historical',
    contests: ['westminster', 'london'],
    description: 'The Communist Party of Great Britain (CPGB) was the principal communist party in Britain throughout the twentieth century. At the 1945 general election it won two seats — Willie Gallacher in West Fife and Phil Piratin in Mile End — its highest ever Westminster representation. The party never again won a seat and was dissolved in 1991.',
  },
  cpb: {
    id: 'cpb', name: 'Communist Party of Britain', shortName: 'CPB',
    color: '#EF0000', dim: 'rgba(239,0,0,0.14)',
    founded: 1988, spectrum: 'Far-left / Communist', isPrimary: false,
    nation: 'others',
    status: 'active',
    contests: ['westminster', 'holyrood', 'senedd'],
    description: 'The Communist Party of Britain (CPB) was established in 1988 by the Communist Party of Great Britain\'s Straight Left / Communist Campaign Group tradition and is the publisher of the Morning Star. Distinct from the dissolved CPGB, it contests Westminster and devolved elections and publishes Britain\'s Road to Socialism.',
  },
  nationalliberal: {
    id: 'nationalliberal', name: 'National Liberal Party', shortName: 'National Liberal',
    color: '#C8B400', dim: 'rgba(200,180,0,0.14)',
    founded: 1931, spectrum: 'Centre / Liberal-Conservative', isPrimary: false,
    nation: 'others',
    description: 'The National Liberal Party formed in 1931 when a faction of the Liberal Party backed the National Government under Ramsay MacDonald. National Liberals generally aligned with the Conservatives in Parliament while maintaining a separate identity. They won 13 seats at the 1945 election before merging with the Conservative Party in 1947–1948.',
  },
  natlibconservative: {
    id: 'natlibconservative', name: 'National Liberal & Conservative', shortName: 'Nat Lib & Con',
    color: '#B8860B', dim: 'rgba(184,134,11,0.14)',
    founded: 1947, spectrum: 'Centre-right / Alliance ticket', isPrimary: false,
    nation: 'others',
    description: 'Joint candidacies between National Liberals and Conservatives, common in the 1950s before the National Liberal organisation was fully absorbed into the Conservative Party. MPs returned on this label sat with the Conservative group in the Commons.',
  },
  ilp: {
    id: 'ilp', name: 'Independent Labour Party', shortName: 'ILP',
    color: '#B22222', dim: 'rgba(178,34,34,0.14)',
    founded: 1893, spectrum: 'Left / Socialist', isPrimary: false,
    nation: 'others',
    description: 'The Independent Labour Party was a founding component of the Labour Party but maintained a separate identity after disaffiliating in 1932. It won three seats at the 1945 general election — its last Westminster representation — before declining further.',
  },
  national: {
    id: 'national', name: 'National Party', shortName: 'National',
    color: '#9CA3AF', dim: 'rgba(156,163,175,0.14)',
    founded: 1945, spectrum: 'Centre / Wartime coalition', isPrimary: false,
    nation: 'others',
    description: 'The National label was used at the 1945 election by candidates associated with the wartime coalition tradition, including Sir John Anderson and Sir Andrew Duncan. It was a short-lived designation rather than a continuing party organisation.',
  },
  irishnationalist: {
    id: 'irishnationalist', name: 'Irish Nationalist', shortName: 'Irish Nationalist',
    color: '#008672', dim: 'rgba(0,134,114,0.14)',
    founded: null, spectrum: 'Nationalist / Irish', isPrimary: false,
    nation: 'northern-ireland',
    description: 'Irish Nationalist MPs represented nationalist communities in Northern Ireland at Westminster, principally in Fermanagh and Tyrone, before the modern SDLP and Sinn Féin became the dominant nationalist parties.',
  },
  nationalindependent: {
    id: 'nationalindependent', name: 'National Independent', shortName: 'National Independent',
    color: '#A8A29E', dim: 'rgba(168,162,158,0.14)',
    founded: null, spectrum: 'Independent / Centre', isPrimary: false,
    nation: 'others',
    description: 'National Independent was an electoral label used by a small number of MPs in the 1940s, often former coalition or independent Conservatives seeking a distinct identity from the main party ticket.',
  },
  indconservative: {
    id: 'indconservative', name: 'Independent Conservative', shortName: 'Ind. Conservative',
    color: '#5B9BD5', dim: 'rgba(91,155,213,0.14)',
    founded: null, spectrum: 'Centre-right / Independent', isPrimary: false,
    nation: 'others',
    description: 'Candidates standing as Independent Conservatives — typically former Conservative MPs or candidates who contested without the official party endorsement while maintaining conservative sympathies.',
  },
  indliberal: {
    id: 'indliberal', name: 'Independent Liberal', shortName: 'Ind. Liberal',
    color: '#E6C200', dim: 'rgba(230,194,0,0.14)',
    founded: null, spectrum: 'Centre / Independent', isPrimary: false,
    nation: 'others',
    description: 'Independent Liberal candidates stood separately from the official Liberal Party organisation, often after disputes over the party\'s direction or local pacts with other parties.',
  },
  indprogressive: {
    id: 'indprogressive', name: 'Independent Progressive', shortName: 'Ind. Progressive',
    color: '#9370DB', dim: 'rgba(147,112,219,0.14)',
    founded: null, spectrum: 'Left / Independent', isPrimary: false,
    nation: 'others',
    description: 'Independent Progressive was an occasional electoral label used by left-leaning independent candidates, including at the 1945 general election.',
  },
  independent: {
    id: 'independent', name: 'Independent', shortName: 'Independent',
    color: '#D1D5DB', dim: 'rgba(209,213,219,0.14)',
    founded: null, spectrum: 'Independent', isPrimary: false,
    nation: 'others',
    description: 'Independent MPs sit without a party whip. Independent university and local candidates have been returned throughout the twentieth century, including notable university seats before their abolition in 1950.',
  },
  speaker: {
    id: 'speaker', name: 'Speaker of the House of Commons', shortName: 'Speaker',
    color: '#C9A84C', dim: 'rgba(201,168,76,0.14)',
    founded: null, spectrum: 'Non-partisan / Presiding officer', isPrimary: false,
    nation: 'others',
    description: 'The Speaker of the House of Commons is elected by MPs to preside over proceedings. By convention the Speaker stands at general elections as "Speaker seeking re-election" rather than under a party label, and the main parties do not normally field candidates against the incumbent.',
  },
  irishlabour: {
    id: 'irishlabour', name: 'Irish Labour', shortName: 'Irish Labour',
    color: '#228B22', dim: 'rgba(34,139,34,0.14)',
    founded: null, spectrum: 'Left / Irish', isPrimary: false,
    nation: 'northern-ireland',
    description: 'Irish Labour contested Northern Ireland seats at Westminster in the early postwar period as a separate organisation from the British Labour Party.',
  },
  irishrepublican: {
    id: 'irishrepublican', name: 'Irish Republican', shortName: 'Irish Republican',
    color: '#006400', dim: 'rgba(0,100,0,0.14)',
    founded: null, spectrum: 'Republican / Irish', isPrimary: false,
    nation: 'northern-ireland',
    description: 'Irish Republican candidates contested Northern Ireland Westminster seats advocating a united Ireland outside the constitutional nationalist tradition.',
  },
  antipartition: {
    id: 'antipartition', name: 'Anti-Partition League', shortName: 'Anti-Partition',
    color: '#2E8B57', dim: 'rgba(46,139,87,0.14)',
    founded: 1945, spectrum: 'Nationalist / Irish', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The Anti-Partition League campaigned against the partition of Ireland and won a Westminster seat at the 1951 general election.',
  },
  republicanlabour: {
    id: 'republicanlabour', name: 'Republican Labour Party', shortName: 'Republican Labour',
    color: '#CD5C5C', dim: 'rgba(205,92,92,0.14)',
    founded: 1964, spectrum: 'Left / Unionist-Labour', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The Republican Labour Party was a small Belfast-based party that won Westminster seats in the 1960s, combining labour politics with a distinct Northern Ireland identity.',
  },
  indunionist: {
    id: 'indunionist', name: 'Independent Unionist', shortName: 'Ind. Unionist',
    color: '#AADFFF', dim: 'rgba(170,223,255,0.14)',
    founded: null, spectrum: 'Unionist / Independent', isPrimary: false,
    nation: 'northern-ireland',
    description: 'Independent Unionist candidates in Northern Ireland stood on a unionist platform without the official Ulster Unionist Party nomination, often reflecting local disputes or hard-line positions.',
  },
  protestantunionist: {
    id: 'protestantunionist', name: 'Protestant Unionist', shortName: 'Protestant Unionist',
    color: '#4169E1', dim: 'rgba(65,105,225,0.14)',
    founded: 1966, spectrum: 'Right / Unionist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The Protestant Unionist label was used by Ian Paisley when he first entered Westminster in 1970, before founding the Democratic Unionist Party.',
  },
  unity: {
    id: 'unity', name: 'Unity', shortName: 'Unity',
    color: '#708090', dim: 'rgba(112,128,144,0.14)',
    founded: null, spectrum: 'Nationalist / Irish', isPrimary: false,
    nation: 'northern-ireland',
    description: 'Unity was an electoral label used by nationalist candidates in Northern Ireland, including at the 1970 general election in Mid Ulster.',
  },
  uuuc: {
    id: 'uuuc', name: 'United Ulster Unionist Council', shortName: 'UUUC',
    color: '#4682B4', dim: 'rgba(70,130,180,0.14)',
    founded: 1974, spectrum: 'Unionist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The United Ulster Unionist Council was an electoral pact of unionist parties opposed to the Sunningdale Agreement. It won most unionist seats at the February 1974 election.',
  },
  ukup: {
    id: 'ukup', name: 'UK Unionist Party', shortName: 'UKUP',
    color: '#5F9EA0', dim: 'rgba(95,158,160,0.14)',
    founded: 1995, spectrum: 'Unionist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The UK Unionist Party was formed by Robert McCartney QC and won a Westminster seat at the 1997 general election on an anti-agreement unionist platform.',
  },
  ulsterpopularunionist: {
    id: 'ulsterpopularunionist', name: 'Ulster Popular Unionist Party', shortName: 'Ulster Popular Unionist',
    color: '#6495ED', dim: 'rgba(100,149,237,0.14)',
    founded: 1980, spectrum: 'Unionist', isPrimary: false,
    nation: 'northern-ireland',
    description: 'The Ulster Popular Unionist Party was a small unionist party led by James Kilfedder, who held North Down from 1983 until his death in 1995.',
  },
  indlabour: {
    id: 'indlabour', name: 'Independent Labour', shortName: 'Ind. Labour',
    color: '#C84B5C', dim: 'rgba(200,75,92,0.14)',
    founded: null, spectrum: 'Left / Independent', isPrimary: false,
    nation: 'others',
    description: 'Candidates standing as Independent Labour — typically former Labour MPs or candidates expelled from or in dispute with the Labour Party.',
  },
  referendumparty: {
    id: 'referendumparty', name: 'Referendum Party', shortName: 'Referendum Party',
    color: '#bf475c', dim: 'rgba(191,71,92,0.14)',
    founded: 1994, spectrum: 'Eurosceptic / Cross-party', isPrimary: false,
    nation: 'others',
    description: 'Founded by billionaire Sir James Goldsmith in 1994, the Referendum Party contested the 1997 general election on a single-issue platform of holding a referendum on Britain\'s membership of the European Union. Despite winning over 800,000 votes (2.6% of the total), the party failed to win a single seat under first-past-the-post. Goldsmith died in July 1997 and the party was dissolved. Its demand for an EU referendum eventually materialised in 2016.',
  },
  bnp: {
    id: 'bnp', name: 'British National Party', shortName: 'BNP',
    color: '#2e3b74', dim: 'rgba(46,59,116,0.14)',
    founded: 1982, spectrum: 'Far-right / Nationalist', isPrimary: false,
    nation: 'others',
    description: 'The British National Party is a far-right, ethno-nationalist party. It achieved its electoral peak in 2009 when it won two European Parliament seats, and in the 2010 Westminster election when it fielded 338 candidates and won 563,743 votes (1.9%). The party has since collapsed, losing its European seats in 2014 and fielding only a handful of candidates thereafter.',
  },
  mebyon: {
    id: 'mebyon', name: 'Mebyon Kernow', shortName: 'Mebyon Kernow',
    color: '#d5c229', dim: 'rgba(213,194,41,0.14)',
    founded: 1951, spectrum: 'Centre-left / Cornish Nationalist', isPrimary: false,
    nation: 'others',
    description: 'Mebyon Kernow (Sons of Cornwall) is a Cornish nationalist and regionalist party that campaigns for a devolved Cornish assembly. It contests elections across Cornwall.',
  },
  omrlp: {
    id: 'omrlp', name: 'Official Monster Raving Loony Party', shortName: 'Monster Raving Loony',
    color: '#FFF000', dim: 'rgba(255,240,0,0.12)',
    founded: 1983, spectrum: 'Satirical', isPrimary: false,
    nation: 'others',
    description: 'Founded by rock musician Screaming Lord Sutch, the OMRLP has contested elections since 1963, often with satirical manifestos. Several of its policies — including the lowering of the voting age to 18 and 24-hour pub licensing — have since been adopted into law.',
  },
  healthconcern: {
    id: 'healthconcern', name: 'Health Concern', shortName: 'Health Concern',
    color: '#FF69B4', dim: 'rgba(255,105,180,0.12)',
    founded: 2001, spectrum: 'Single-issue', isPrimary: false,
    nation: 'others',
    description: 'Health Concern was formed in 2001 by Dr Richard Taylor to campaign against the reconfiguration of Kidderminster Hospital. Taylor won the Wyre Forest constituency in 2001 and 2005 as an independent / Health Concern candidate.',
  },
  tusc: {
    id: 'tusc', name: 'Trade Unionist and Socialist Coalition', shortName: 'TUSC',
    color: '#EC008C', dim: 'rgba(236,0,140,0.12)',
    founded: 2010, spectrum: 'Left / Socialist', isPrimary: false,
    nation: 'others',
    description: 'TUSC is an electoral coalition of socialist and trade union groups formed ahead of the 2010 general election. It contests elections as a left-wing alternative to Labour.',
  },
  workersparty: {
    id: 'workersparty', name: 'Workers Party of Britain', shortName: 'Workers Party',
    color: '#780021', dim: 'rgba(120,0,33,0.14)',
    founded: 2019, spectrum: 'Left / Populist', isPrimary: false,
    nation: 'others',
    description: 'The Workers Party of Britain was founded by George Galloway, previously of Respect and the Labour Party. Galloway won the Rochdale by-election in February 2024 but lost his seat in the general election five months later. The party ran candidates across the country on a socially conservative, anti-war platform.',
  },
  restorebrit: {
    id: 'restorebrit', name: 'Restore Britain', shortName: 'Restore Britain',
    color: '#062754', dim: 'rgba(6,39,84,0.12)',
    founded: 2024, spectrum: 'Right / Nationalist', isPrimary: false,
    nation: 'others',
    description: 'Restore Britain is a right-wing party contesting elections from 2024.',
  },
  yourparty: {
    id: 'yourparty', name: 'Your Party (UK)', shortName: 'Your Party',
    color: '#FF3131', dim: 'rgba(255,49,49,0.12)',
    founded: 2020, spectrum: 'Populist', isPrimary: false,
    nation: 'others',
    description: 'Your Party is a small UK political party.',
  },
  ssp: {
    id: 'ssp', name: 'Scottish Socialist Party', shortName: 'SSP',
    color: '#c41230', dim: 'rgba(196,18,48,0.14)',
    founded: 1998, spectrum: 'Left / Scottish Nationalist', isPrimary: false,
    nation: 'others',
    description: 'The Scottish Socialist Party was founded in 1998 and achieved its peak at the 2003 Scottish Parliament election, winning six MSPs on a platform of Scottish independence and socialist policies. The party contested Westminster elections but never won a seat. Internal divisions following the Tommy Sheridan defamation case in 2006 led to a split and rapid decline.',
  },
  respect: {
    id: 'respect', name: 'Respect Party', shortName: 'Respect',
    color: '#c1272d', dim: 'rgba(193,39,45,0.14)',
    founded: 2004, spectrum: 'Left / Anti-war', isPrimary: false,
    nation: 'others',
    description: 'The Respect Party was founded in 2004 as a left-wing, anti-war coalition, emerging largely in opposition to the Iraq War. Its most prominent figure was George Galloway, who won Bethnal Green and Bow from Labour in 2005 — one of the most dramatic upsets of that election. Galloway later won the Bradford West by-election in 2012. The party disbanded in 2016.',
  },
  wep: {
    id: 'wep', name: "Women's Equality Party", shortName: "Women's Equality Party",
    color: '#582C83', dim: 'rgba(88,44,131,0.14)',
    founded: 2015, spectrum: 'Centre / Feminist', isPrimary: false,
    nation: 'others',
    description: "The Women's Equality Party was founded in 2015 by journalist Catherine Mayer and comedian Sandi Toksvig, emerging from a public meeting that attracted several thousand responses. The party campaigns across six core objectives: equal representation in politics and business, equal pay, equal education, shared parenting and caregiving, equal media treatment, and an end to violence against women. It fielded candidates in the 2016 London Assembly election and the 2017 general election. The party positions itself as cross-partisan, arguing that gender equality benefits everyone regardless of political affiliation.",
  },
  cooperative: {
    id: 'cooperative', name: 'Co-operative Party', shortName: 'Co-operative Party',
    color: '#6B2D8B', dim: 'rgba(107,45,139,0.14)',
    founded: 1917, spectrum: 'Centre-left / Co-operative', isPrimary: false,
    nation: 'others',
    description: 'The Co-operative Party was founded in 1917 by the Co-operative movement to represent its interests in Parliament. It has operated in electoral alliance with the Labour Party since 1927, and its MPs sit as "Labour and Co-operative" members. The party campaigns for co-operative and mutual ownership models, ethical business, fair trade, and social justice. It is one of the oldest continuously active parties in British politics, and regularly returns around 20–30 MPs who hold dual Labour/Co-operative endorsement.',
  },
  nha: {
    id: 'nha', name: 'National Health Action Party', shortName: 'National Health Action',
    color: '#005EB8', dim: 'rgba(0,94,184,0.14)',
    founded: 2012, spectrum: 'Centre-left / Single-issue', isPrimary: false,
    nation: 'others',
    description: 'The National Health Action Party was founded in 2012 by NHS consultants and campaigners, including Dr Clive Peedell and Dr Richard Taylor (formerly of Health Concern), in opposition to the Health and Social Care Act 2012, which they argued would fragment and privatise the NHS. The party contests elections on a platform of defending publicly funded healthcare, reversing NHS privatisation, and protecting frontline services. It fielded candidates in the 2015 and 2017 general elections.',
  },
  pirate: {
    id: 'pirate', name: 'Pirate Party UK', shortName: 'Pirate Party UK',
    color: '#FF6600', dim: 'rgba(255,102,0,0.14)',
    founded: 2009, spectrum: 'Libertarian / Digital rights', isPrimary: false,
    nation: 'others',
    description: 'Pirate Party UK was founded in 2009 as part of the international Pirate Party movement, which originated in Sweden in 2006. The party campaigns for digital rights, civil liberties, copyright and patent reform, net neutrality, privacy, and government transparency. It fielded candidates in the 2010, 2015 and 2017 general elections, never winning a Westminster seat. The party produced crowd-sourced, openly licensed manifestos — its 2015 document invited public contributions via Reddit, and its 2017 "Open Manifesto" was released under a Creative Commons zero licence. Pirate Party UK was dissolved in 2020.',
  },
  cista: {
    id: 'cista', name: 'Cannabis Is Safer Than Alcohol', shortName: 'CISTA',
    color: '#2E8B57', dim: 'rgba(46,139,87,0.14)',
    founded: 2015, spectrum: 'Single-issue / Drug reform', isPrimary: false,
    nation: 'others',
    description: 'Cannabis Is Safer Than Alcohol (CISTA) was registered as a political party in March 2015 under leader Paul Birch to campaign for evidence-based drug-law reform, starting with the legal regulation of cannabis. It fielded 32 candidates across England, Scotland, Wales and Northern Ireland at the 2015 general election — the first pro-reform single-issue party to contest seats in all four nations — and fielded Lee Harris as its candidate for Mayor of London in 2016.',
  },
  // London mayoral minor / persona brands (folder slug = party id)
  binface: {
    id: 'binface', name: 'Count Binface', shortName: 'Count Binface',
    color: '#6B7280', dim: 'rgba(107,114,128,0.14)',
    founded: 2018, spectrum: 'Satirical / Independent', isPrimary: false,
    nation: 'others',
    description: 'Count Binface is a satirical persona who has contested the London mayoral election, publishing short manifesto texts that parody the serious candidates.',
  },
  londonreal: {
    id: 'londonreal', name: 'London Real Party', shortName: 'London Real',
    color: '#111827', dim: 'rgba(17,24,39,0.14)',
    founded: 2020, spectrum: 'Independent / Media', isPrimary: false,
    nation: 'others',
    description: 'The London Real Party was founded by podcaster Brian Rose and contested the 2021 and 2024 London mayoral elections.',
  },
  reclaim: {
    id: 'reclaim', name: 'Reclaim Party', shortName: 'Reclaim',
    color: '#1D4ED8', dim: 'rgba(29,78,216,0.14)',
    founded: 2020, spectrum: 'Right / Populist', isPrimary: false,
    nation: 'others',
    description: 'The Reclaim Party was founded by actor Laurence Fox and contested the 2021 London mayoral election on a free-speech and anti-lockdown platform.',
  },
  britainfirst: {
    id: 'britainfirst', name: 'Britain First', shortName: 'Britain First',
    color: '#166534', dim: 'rgba(22,101,52,0.14)',
    founded: 2011, spectrum: 'Far-right / Nationalist', isPrimary: false,
    nation: 'others',
    description: 'Britain First is a far-right British nationalist party that has contested London mayoral and other elections.',
  },
  burningpink: {
    id: 'burningpink', name: 'Burning Pink', shortName: 'Burning Pink',
    color: '#EC4899', dim: 'rgba(236,72,153,0.14)',
    founded: 2020, spectrum: 'Environmentalist / Protest', isPrimary: false,
    nation: 'others',
    description: 'Burning Pink (Beyond Politics) is an environmentalist protest party that fielded Valerie Brown as its candidate for Mayor of London in 2021.',
  },
  onelove: {
    id: 'onelove', name: 'One Love Party', shortName: 'One Love',
    color: '#F59E0B', dim: 'rgba(245,158,11,0.14)',
    founded: 2016, spectrum: 'Independent / Single-issue', isPrimary: false,
    nation: 'others',
    description: 'The One Love Party fielded Ankit Love as its candidate for Mayor of London in 2016.',
  },
  pierscorbyn: {
    id: 'pierscorbyn', name: 'Let London Live', shortName: 'Let London Live',
    color: '#DC2626', dim: 'rgba(220,38,38,0.14)',
    founded: 2021, spectrum: 'Independent / Anti-lockdown', isPrimary: false,
    nation: 'others',
    description: 'Let London Live was the ballot label used by weather forecaster Piers Corbyn when he contested the 2021 London mayoral election.',
  },
  changeuk: {
    id: 'changeuk', name: 'Change UK', shortName: 'Change UK',
    color: '#3B5998', dim: 'rgba(59,89,152,0.14)',
    founded: 2019, spectrum: 'Centre / Pro-European', isPrimary: false,
    nation: 'england',
    description: 'Change UK (originally The Independent Group) was formed in 2019 by MPs who defected from Labour and the Conservatives in opposition to their leaders’ positions on Brexit. It contested the 2019 European Parliament election but failed to win any seats and was dissolved shortly after.',
  },
  animalpolitics: {
    id: 'animalpolitics', name: 'Animal Welfare Party', shortName: 'Animal Welfare',
    color: '#76B82A', dim: 'rgba(118,184,42,0.14)',
    founded: 2006, spectrum: 'Left / Animal Rights', isPrimary: false,
    nation: 'others',
    description: 'The Animal Welfare Party (contesting as Animal Politics EU in 2019) is a minor party advocating for animal rights, health, and environmental protection.',
  },
  sand: {
    id: 'sand', name: 'Progressive Alliance of Socialists and Democrats', shortName: 'S&D',
    color: '#E4003B', dim: 'rgba(228,0,59,0.14)',
    founded: 2009, spectrum: 'Centre-left / Social Democratic', isPrimary: false,
    nation: 'europe',
    description: 'The Progressive Alliance of Socialists and Democrats (S&D) is the social democratic group in the European Parliament. Its lineage runs from the Socialist Group (1979) through the Party of European Socialists (PES) to S&D from 2009. UK Labour sat in this family throughout direct elections.',
  },
  renew: {
    id: 'renew', name: 'Renew Europe', shortName: 'Renew Europe',
    color: '#FFD700', dim: 'rgba(255,215,0,0.14)',
    founded: 2019, spectrum: 'Centre / Liberal', isPrimary: false,
    nation: 'europe',
    description: 'Renew Europe is the liberal and centrist group in the European Parliament from 2019. Its lineage runs from the Liberal and Democratic Group through LDR, ELDR, and ALDE. UK Liberal Democrats sat in this family throughout direct elections.',
  },
  epp: {
    id: 'epp', name: "European People's Party Group", shortName: 'EPP',
    color: '#003399', dim: 'rgba(0,51,153,0.14)',
    founded: 1976, spectrum: 'Centre-right / Christian Democratic', isPrimary: false,
    nation: 'europe',
    description: "The European People's Party (EPP) group brings together centre-right and Christian democratic parties. From 1999 to 2009 many UK Conservatives sat in the EPP-ED configuration before the conservative split that created ECR.",
  },
  greensefa: {
    id: 'greensefa', name: 'Greens/European Free Alliance Group', shortName: 'Greens/EFA',
    color: '#009639', dim: 'rgba(0,150,57,0.14)',
    founded: 1999, spectrum: 'Left / Green / Regionalist', isPrimary: false,
    nation: 'europe',
    description: 'Greens/EFA combines green and regionalist parties in the European Parliament from 1999, succeeding earlier Green Group and Rainbow/EFA arrangements. UK Green, SNP, Plaid Cymru, and related parties sat in this family.',
  },
  guengl: {
    id: 'guengl', name: 'The Left group in the European Parliament', shortName: 'GUE/NGL',
    color: '#E30613', dim: 'rgba(227,6,19,0.14)',
    founded: 1995, spectrum: 'Left', isPrimary: false,
    nation: 'europe',
    description: 'GUE/NGL (The Left) is the radical-left group in the European Parliament, formed from communist and socialist traditions including the Communist and Allies Group, European United Left, and Nordic Green Left.',
  },
  ecr: {
    id: 'ecr', name: 'European Conservatives and Reformists Group', shortName: 'ECR',
    color: '#1B3A6B', dim: 'rgba(27,58,107,0.14)',
    founded: 2009, spectrum: 'Right / Eurosceptic', isPrimary: false,
    nation: 'europe',
    description: 'The European Conservatives and Reformists (ECR) group was formed in 2009 when British and Czech conservatives broke from the EPP-ED line. It continues the British/Danish conservative Eurosceptic tradition in the Parliament.',
  },
  identity: {
    id: 'identity', name: 'Identity and Democracy', shortName: 'ID',
    color: '#003366', dim: 'rgba(0,51,102,0.14)',
    founded: 2019, spectrum: 'Right / Nationalist', isPrimary: false,
    nation: 'europe',
    description: 'Identity and Democracy (ID) is the far-right nationalist group in the European Parliament from 2019, succeeding the Europe of Nations and Freedom (ENF) line. Earlier manifestations include the European Right and short-lived alliances such as the European Alliance for Freedom.',
  },
  inddem: {
    id: 'inddem', name: 'Hard Eurosceptic / Direct-Democracy Groups', shortName: 'Eurosceptic groups',
    color: '#70147A', dim: 'rgba(112,20,122,0.14)',
    founded: 1994, spectrum: 'Right / Eurosceptic', isPrimary: false,
    nation: 'europe',
    description: 'Hard Eurosceptic groups in the European Parliament evolved through Europe of Nations, EDD, Independence/Democracy, EFD, and EFDD. UKIP and allies sat in this line before it failed to re-form in 2019.',
  },
  uen: {
    id: 'uen', name: 'Gaullist / National-Conservative Groups', shortName: 'UEN line',
    color: '#0054A6', dim: 'rgba(0,84,166,0.14)',
    founded: 1979, spectrum: 'Right / Nationalist', isPrimary: false,
    nation: 'europe',
    description: 'National-conservative groups in the European Parliament ran from European Progressive Democrats and European Democratic Alliance through Union for Europe and Union for Europe of the Nations (UEN), dissolved in 2009.',
  },
  diem25: {
    id: 'diem25', name: 'Democracy in Europe Movement 2025', shortName: 'DiEM25',
    color: '#E30613', dim: 'rgba(227,6,19,0.14)',
    founded: 2016, spectrum: 'Left / Pro-European', isPrimary: false,
    nation: 'europe',
    description: 'DiEM25 (Democracy in Europe Movement 2025) is a pan-European political movement founded by Yanis Varoufakis, advocating democratic reform of the EU.',
  },
  ecpm: {
    id: 'ecpm', name: 'European Christian Political Movement', shortName: 'ECPM',
    color: '#0055A5', dim: 'rgba(0,85,165,0.14)',
    founded: 2002, spectrum: 'Centre-right / Christian', isPrimary: false,
    nation: 'europe',
    description: 'The European Christian Political Movement (ECPM) is a European political party of Christian democratic and socially conservative parties.',
  },
  eurpirates: {
    id: 'eurpirates', name: 'European Pirate Party', shortName: 'European Pirates',
    color: '#592880', dim: 'rgba(89,40,128,0.14)',
    founded: 2010, spectrum: 'Centre / Pirate', isPrimary: false,
    nation: 'england',
    description: 'The European Pirate Party is the federation of pirate parties across Europe, campaigning on civil liberties, transparency, and digital rights.',
  },
  volt: {
    id: 'volt', name: 'Volt Europa', shortName: 'Volt',
    color: '#502BD5', dim: 'rgba(80,43,213,0.14)',
    founded: 2017, spectrum: 'Centre / Pro-European', isPrimary: false,
    nation: 'europe',
    description: 'Volt Europa is a pan-European political movement advocating federal reform of the European Union. It contested the 2019 European Parliament election.',
  },
  englishdemocrats: {
    id: 'englishdemocrats', name: 'English Democrats', shortName: 'English Democrats',
    color: '#E4003B', dim: 'rgba(228,0,59,0.14)',
    founded: 2002, spectrum: 'Right-wing / English Nationalist', isPrimary: false,
    nation: 'others',
    description: 'The English Democrats are a right-wing English nationalist party campaigning for an independent England or an English Parliament.',
  },
  christian: {
    id: 'christian', name: 'Christian Party / CPA', shortName: 'Christian Party',
    color: '#0055A5', dim: 'rgba(0,85,165,0.14)',
    founded: 2004, spectrum: 'Right / Christian', isPrimary: false,
    nation: 'england',
    description: 'The Christian Party and Christian People\'s Alliance are social-conservative political parties campaigning on a Christian platform.',
  },
  cpa: {
    id: 'cpa', name: 'Christian Peoples Alliance', shortName: 'CPA',
    color: '#0055A5', dim: 'rgba(0,85,165,0.14)',
    founded: 1999, spectrum: 'Right / Christian', isPrimary: false,
    nation: 'others',
    description: 'The Christian Peoples Alliance is a social-conservative party founded in 1999. It contests elections on a Christian-democratic platform and has fielded candidates in Westminster and London elections.',
  },
  stuckist: {
    id: 'stuckist', name: 'Stuckist Party', shortName: 'Stuckist',
    color: '#C41E3A', dim: 'rgba(196,30,58,0.14)',
    founded: 2001, spectrum: 'Arts / Anti-establishment', isPrimary: false,
    nation: 'others',
    description: 'The Stuckist Party grew out of the Stuckist art movement and contested the 2001 general election with a manifesto opposing conceptual art orthodoxy and championing painting.',
  },
  veritas: {
    id: 'veritas', name: 'Veritas', shortName: 'Veritas',
    color: '#6B2D8B', dim: 'rgba(107,45,139,0.14)',
    founded: 2005, spectrum: 'Right / Populist', isPrimary: false,
    nation: 'others',
    description: 'Veritas was founded by Robert Kilroy-Silk in 2005 after he left UKIP. The party contested the 2005 general election on a populist, Eurosceptic platform before fading.',
  },
  forwardwales: {
    id: 'forwardwales', name: 'Forward Wales', shortName: 'Forward Wales',
    color: '#C8102E', dim: 'rgba(200,16,46,0.14)',
    founded: 2003, spectrum: 'Left / Welsh', isPrimary: false,
    nation: 'wales',
    description: 'Forward Wales (Cymru Ymlaen) was a left-wing Welsh party founded by John Marek after leaving Labour. It contested the 2005 general election and the National Assembly before dissolving.',
  },
  socialistalternative: {
    id: 'socialistalternative', name: 'Socialist Alternative', shortName: 'Socialist Alternative',
    color: '#EB1C23', dim: 'rgba(235,28,35,0.14)',
    founded: 2014, spectrum: 'Left / Socialist', isPrimary: false,
    nation: 'others',
    description: 'Socialist Alternative is a Trotskyist organisation that has contested UK elections, including the 2015 general election, on an anti-austerity socialist platform.',
  },
  socialistlabour: {
    id: 'socialistlabour', name: 'Socialist Labour Party', shortName: 'Socialist Labour',
    color: '#9B1B30', dim: 'rgba(155,27,48,0.14)',
    founded: 1996, spectrum: 'Left / Socialist', isPrimary: false,
    nation: 'others',
    description: 'The Socialist Labour Party was founded in 1996 by Arthur Scargill after he left the Labour Party. It campaigns for public ownership, trade union rights, and a socialist programme, and is distinct from Labour, the Scottish Socialist Party, Socialist Alternative, and TUSC.',
  },
  liberal1989: {
    id: 'liberal1989', name: 'Liberal Party (1989–)', shortName: 'Liberal Party',
    color: '#FFD700', dim: 'rgba(255,215,0,0.14)',
    founded: 1989, spectrum: 'Centre / Liberal', isPrimary: false,
    nation: 'others',
    description: 'The Liberal Party was formed in 1989 by members of the former Liberal Party who opposed its merger with the SDP. It is a distinct contemporary party from the Liberal Democrats and continues to contest general elections on a liberal platform.',
  },
  sdp: {
    id: 'sdp', name: 'Social Democratic Party', shortName: 'SDP',
    color: '#E31C79', dim: 'rgba(227,28,121,0.14)',
    founded: 1990, spectrum: 'Centre / Social Democratic', isPrimary: false,
    nation: 'others',
    description: 'The modern Social Democratic Party continues the SDP name after the 1980s party merged into the Liberal Democrats. It contests elections on a social-democratic, culturally conservative platform.',
  },
  yorkshire: {
    id: 'yorkshire', name: 'Yorkshire Party', shortName: 'Yorkshire Party',
    color: '#00AEEF', dim: 'rgba(0,174,239,0.14)',
    founded: 2014, spectrum: 'Regionalist', isPrimary: false,
    nation: 'others',
    description: 'The Yorkshire Party campaigns for a directly elected parliament for Yorkshire and greater regional devolution. It has contested Westminster, local and European elections.',
  },
  rejoin: {
    id: 'rejoin', name: 'Rejoin EU', shortName: 'Rejoin EU',
    color: '#003399', dim: 'rgba(0,51,153,0.14)',
    founded: 2020, spectrum: 'Centre / Pro-European', isPrimary: false,
    nation: 'others',
    description: 'Rejoin EU campaigns for the United Kingdom to rejoin the European Union. It contested the 2024 general election on a single-issue pro-European platform.',
  },
  aontu: {
    id: 'aontu', name: 'Aontú', shortName: 'Aontú',
    color: '#445C2A', dim: 'rgba(68,92,42,0.14)',
    founded: 2019, spectrum: 'Centre / Irish Republican', isPrimary: false,
    nation: 'northern-ireland',
    description: 'Aontú is an all-Ireland republican party founded by Peadar Tóibín after leaving Sinn Féin. It contests elections in Northern Ireland and the Republic on a socially conservative, anti-abortion platform.',
  },
  /* Brexit Party → Reform UK via PARTY_ALIASES (euro/2019/brexit folder slug retained). */
  others: {
    id: 'others', name: 'Others', shortName: 'Others',
    color: '#6b7280', dim: 'rgba(107,114,128,0.14)',
    founded: null, spectrum: 'Various', isPrimary: false,
    nation: null,
    description: 'Independents, minor parties, and candidates not separately categorised.',
  },
};

/* ── Nation overview data (sourced from HC Library CBP-7529) ── */
const NATIONS = {
  england: {
    id: 'england',
    name: 'England',
    constituencies: 543,
    electoralSystem: 'First Past the Post',
    devolvedBody: null,
    devolvedYear: null,
    description: 'England returns 543 of the 650 Westminster MPs (following 2023 boundary changes). Unlike Wales, Scotland and Northern Ireland, England has no separate devolved parliament — a long-standing political debate known as the "West Lothian Question." Regional devolution exists through elected metro-mayors (Greater Manchester, West Midlands, etc.), with powers over transport, housing and economic development. The 2004 North East England referendum rejected a regional assembly by 78% to 22%.',
    keyFacts: [
      'England elects 543 of 650 Westminster MPs — 83.5% of the total',
      'No English Parliament: the only part of the UK without devolution',
      'English Votes for English Laws (EVEL) procedure introduced 2015, abolished 2021',
      'Elected metro-mayors introduced from 2017 for combined authority areas',
      'North East England voted 78% against a regional assembly in 2004',
    ],
    westminsterResults: [
      { year: '1918',     con: 315, lab:  42, ld: 107, other:  21, total: 485 },
      { year: '1922',     con: 307, lab:  95, ld:  75, other:   8, total: 485 },
      { year: '1923',     con: 221, lab: 138, ld: 123, other:   3, total: 485 },
      { year: '1924',     con: 347, lab: 109, ld:  19, other:  10, total: 485 },
      { year: '1929',     con: 221, lab: 226, ld:  35, other:   3, total: 485 },
      { year: '1931',     con: 436, lab:  29, ld:  19, other:   1, total: 485 },
      { year: '1935',     con: 357, lab: 116, ld:  11, other:   1, total: 485 },
      { year: '1945',     con: 167, lab: 331, ld:   5, other:   7, total: 510 },
      { year: '1950',     con: 253, lab: 251, ld:   2, other:   0, total: 506 },
      { year: '1951',     con: 271, lab: 233, ld:   2, other:   0, total: 506 },
      { year: '1955',     con: 293, lab: 216, ld:   2, other:   0, total: 511 },
      { year: '1959',     con: 315, lab: 193, ld:   3, other:   0, total: 511 },
      { year: '1964',     con: 262, lab: 246, ld:   3, other:   0, total: 511 },
      { year: '1966',     con: 219, lab: 285, ld:   6, other:   1, total: 511 },
      { year: '1970',     con: 292, lab: 216, ld:   2, other:   1, total: 511 },
      { year: 'Feb 1974', con: 268, lab: 237, ld:   9, other:   2, total: 516 },
      { year: 'Oct 1974', con: 253, lab: 255, ld:   8, other:   0, total: 516 },
      { year: '1979',     con: 306, lab: 203, ld:   7, other:   0, total: 516 },
      { year: '1983',     con: 362, lab: 148, ld:  13, other:   0, total: 523 },
      { year: '1987',     con: 358, lab: 155, ld:  10, other:   0, total: 523 },
      { year: '1992',     con: 319, lab: 195, ld:  10, other:   0, total: 524 },
      { year: '1997',     con: 165, lab: 328, ld:  34, other:   2, total: 529 },
      { year: '2001',     con: 165, lab: 323, ld:  40, other:   1, total: 529 },
      { year: '2005',     con: 194, lab: 286, ld:  47, other:   2, total: 529 },
      { year: '2010',     con: 297, lab: 191, ld:  43, other:   2, total: 533 },
      { year: '2015',     con: 318, lab: 206, ld:   6, other:   3, total: 533 },
      { year: '2017',     con: 296, lab: 227, ld:   8, other:   2, total: 533 },
      { year: '2019',     con: 345, lab: 179, ld:   7, other:   2, total: 533 },
      { year: '2024',     con: 116, lab: 347, ld:  65, other:  15, total: 543 },
    ],
    source: 'HC Library Research Briefing CBP-7529, UK Election Statistics 1918–2023',
  },
  wales: {
    id: 'wales',
    name: 'Wales',
    constituencies: 32,
    electoralSystem: 'First Past the Post (Westminster); Additional Member System (Senedd)',
    devolvedBody: 'Senedd Cymru (Welsh Parliament)',
    devolvedYear: 1999,
    description: 'Wales returns 32 Westminster MPs following 2023 boundary changes (reduced from 40). The Senedd Cymru — Welsh Parliament — was established in 1999 after a referendum in which 50.3% voted Yes on a margin of just 6,721 votes. The Senedd uses the Additional Member System: 40 constituency and 20 regional members are elected. Labour has always been the largest party in the Senedd, though it has never won an outright majority. Plaid Cymru achieved its best result in 1999 (30% of the vote, 17 seats). Subject to legislation, from 2026 the Senedd will expand to 96 members elected under a new system.',
    keyFacts: [
      '1997 Welsh devolution referendum: 50.3% Yes on a margin of 6,721 votes',
      'Senedd established 1999; name changed from National Assembly for Wales in 2020',
      '60 Senedd Members (40 constituency + 20 regional), expanding to 96 in 2026',
      'Labour has been the largest party at every Senedd election since 1999',
      'Plaid Cymru\'s best result: 1999 — 28% of vote, 17 seats',
      'In 2003, an equal number of male and female Members were elected to the Assembly',
    ],
    seneddResults: [
      { year: 1999, lab: 28, pc: 17, con: 9, ld: 6, reform: 0, others: 0 },
      { year: 2003, lab: 30, pc: 12, con: 11, ld: 6, reform: 0, others: 1 },
      { year: 2007, lab: 26, pc: 15, con: 12, ld: 6, reform: 0, others: 1 },
      { year: 2011, lab: 30, pc: 11, con: 14, ld: 5, reform: 0, others: 0 },
      { year: 2016, lab: 29, pc: 12, con: 11, ld: 1, ukip: 7, reform: 0, others: 0 },
      { year: 2021, lab: 30, pc: 13, con: 16, ld: 1, reform: 0, others: 0 },
      { year: 2026, lab: 9, pc: 43, con: 7, ld: 1, grn: 2, reform: 34, others: 0 },
    ],
    westminsterResults: [
      { year: '1918',     con:  4, lab:  9, ld: 20, pc: 0, other: 2, total: 35 },
      { year: '1922',     con:  6, lab: 18, ld: 10, pc: 0, other: 1, total: 35 },
      { year: '1923',     con:  4, lab: 19, ld: 11, pc: 0, other: 1, total: 35 },
      { year: '1924',     con:  9, lab: 16, ld: 10, pc: 0, other: 0, total: 35 },
      { year: '1929',     con:  1, lab: 25, ld:  9, pc: 0, other: 0, total: 35 },
      { year: '1931',     con: 11, lab: 16, ld:  8, pc: 0, other: 0, total: 35 },
      { year: '1935',     con: 11, lab: 18, ld:  6, pc: 0, other: 0, total: 35 },
      { year: '1945',     con:  4, lab: 25, ld:  6, pc: 0, other: 0, total: 35 },
      { year: '1950',     con:  4, lab: 27, ld:  5, pc: 0, other: 0, total: 36 },
      { year: '1951',     con:  6, lab: 27, ld:  3, pc: 0, other: 0, total: 36 },
      { year: '1955',     con:  6, lab: 27, ld:  3, pc: 0, other: 0, total: 36 },
      { year: '1959',     con:  7, lab: 27, ld:  2, pc: 0, other: 0, total: 36 },
      { year: '1964',     con:  6, lab: 28, ld:  2, pc: 0, other: 0, total: 36 },
      { year: '1966',     con:  3, lab: 32, ld:  1, pc: 0, other: 0, total: 36 },
      { year: '1970',     con:  7, lab: 27, ld:  1, pc: 0, other: 1, total: 36 },
      { year: 'Feb 1974', con:  8, lab: 24, ld:  2, pc: 2, other: 0, total: 36 },
      { year: 'Oct 1974', con:  8, lab: 23, ld:  2, pc: 3, other: 0, total: 36 },
      { year: '1979',     con: 11, lab: 22, ld:  1, pc: 2, other: 0, total: 36 },
      { year: '1983',     con: 14, lab: 20, ld:  2, pc: 2, other: 0, total: 38 },
      { year: '1987',     con:  8, lab: 24, ld:  3, pc: 3, other: 0, total: 38 },
      { year: '1992',     con:  6, lab: 27, ld:  1, pc: 4, other: 0, total: 38 },
      { year: '1997',     con:  0, lab: 34, ld:  2, pc: 4, other: 0, total: 40 },
      { year: '2001',     con:  0, lab: 34, ld:  2, pc: 4, other: 0, total: 40 },
      { year: '2005',     con:  3, lab: 29, ld:  4, pc: 3, other: 1, total: 40 },
      { year: '2010',     con:  8, lab: 26, ld:  3, pc: 3, other: 0, total: 40 },
      { year: '2015',     con: 11, lab: 25, ld:  1, pc: 3, other: 0, total: 40 },
      { year: '2017',     con:  8, lab: 28, ld:  0, pc: 4, other: 0, total: 40 },
      { year: '2019',     con: 14, lab: 22, ld:  0, pc: 4, other: 0, total: 40 },
      { year: '2024',     con:  0, lab: 27, ld:  1, pc: 4, other: 0, total: 32 },
    ],
    source: 'HC Library Research Briefing CBP-7529, UK Election Statistics 1918–2023',
  },
  scotland: {
    id: 'scotland',
    name: 'Scotland',
    constituencies: 57,
    electoralSystem: 'First Past the Post (Westminster); Additional Member System (Holyrood)',
    devolvedBody: 'Scottish Parliament',
    devolvedYear: 1999,
    description: 'Scotland returns 57 Westminster MPs following 2023 boundary changes. The Scottish Parliament at Holyrood was established in 1999 after a 1997 referendum in which 74.3% voted for a parliament and 63.5% voted for tax-varying powers. Holyrood has 129 Members of the Scottish Parliament (MSPs): 73 constituency and 56 regional, elected every five years under the Additional Member System. Labour won the most seats in the first two Holyrood elections (1999, 2003) and governed in coalition with the Liberal Democrats. The SNP replaced Labour as the largest party in 2007 and has governed Scotland continuously since. In the 2014 independence referendum, 55.3% voted to remain in the United Kingdom.',
    keyFacts: [
      '1997 devolution referendum: 74.3% voted Yes for a parliament, 63.5% for tax powers',
      'Scottish Parliament established 1999; SNP has governed since 2007',
      '129 MSPs (73 constituency + 56 regional), elected every 5 years',
      'SNP won 56 of 59 Westminster seats at the 2015 general election',
      '2014 independence referendum: 55.3% voted No to independence',
      'Scottish Green Party entered co-operation agreement with SNP government in 2021',
    ],
    holyroodResults: [
      { year: 1999, snp: 35, lab: 56, con: 18, ld: 17, grn: 1, reform: 0, others: 2 },
      { year: 2003, snp: 27, lab: 50, con: 18, ld: 17, grn: 7, reform: 0, others: 10 },
      { year: 2007, snp: 47, lab: 46, con: 17, ld: 16, grn: 2, reform: 0, others: 1 },
      { year: 2011, snp: 69, lab: 37, con: 15, ld: 5, grn: 2, reform: 0, others: 1 },
      { year: 2016, snp: 63, lab: 24, con: 31, ld: 5, grn: 6, reform: 0, others: 0 },
      { year: 2021, snp: 64, lab: 22, con: 31, ld: 4, grn: 7, reform: 0, others: 1 },
      { year: 2026, snp: 58, lab: 17, con: 12, ld: 10, grn: 15, reform: 17, others: 0 },
    ],
    westminsterResults: [
      { year: '1918',     con: 30, lab:  6, ld: 33, snp: 0, other: 2, total: 71 },
      { year: '1922',     con: 13, lab: 29, ld: 27, snp: 0, other: 2, total: 71 },
      { year: '1923',     con: 14, lab: 34, ld: 22, snp: 0, other: 1, total: 71 },
      { year: '1924',     con: 36, lab: 26, ld:  8, snp: 0, other: 1, total: 71 },
      { year: '1929',     con: 20, lab: 36, ld: 13, snp: 0, other: 2, total: 71 },
      { year: '1931',     con: 57, lab:  7, ld:  7, snp: 0, other: 0, total: 71 },
      { year: '1935',     con: 43, lab: 20, ld:  3, snp: 0, other: 5, total: 71 },
      { year: '1945',     con: 27, lab: 37, ld:  0, snp: 0, other: 7, total: 71 },
      { year: '1950',     con: 31, lab: 37, ld:  2, snp: 0, other: 1, total: 71 },
      { year: '1951',     con: 35, lab: 35, ld:  1, snp: 0, other: 0, total: 71 },
      { year: '1955',     con: 36, lab: 34, ld:  1, snp: 0, other: 0, total: 71 },
      { year: '1959',     con: 31, lab: 38, ld:  1, snp: 0, other: 1, total: 71 },
      { year: '1964',     con: 24, lab: 43, ld:  4, snp: 0, other: 0, total: 71 },
      { year: '1966',     con: 20, lab: 46, ld:  5, snp: 0, other: 0, total: 71 },
      { year: '1970',     con: 23, lab: 44, ld:  3, snp: 1, other: 0, total: 71 },
      { year: 'Feb 1974', con: 21, lab: 40, ld:  3, snp: 7, other: 0, total: 71 },
      { year: 'Oct 1974', con: 16, lab: 41, ld:  3, snp:11, other: 0, total: 71 },
      { year: '1979',     con: 22, lab: 44, ld:  3, snp: 2, other: 0, total: 71 },
      { year: '1983',     con: 21, lab: 41, ld:  8, snp: 2, other: 0, total: 72 },
      { year: '1987',     con: 10, lab: 50, ld:  9, snp: 3, other: 0, total: 72 },
      { year: '1992',     con: 11, lab: 49, ld:  9, snp: 3, other: 0, total: 72 },
      { year: '1997',     con:  0, lab: 56, ld: 10, snp: 6, other: 0, total: 72 },
      { year: '2001',     con:  1, lab: 55, ld: 10, snp: 5, other: 1, total: 72 },
      { year: '2005',     con:  1, lab: 40, ld: 11, snp: 6, other: 1, total: 59 },
      { year: '2010',     con:  1, lab: 41, ld: 11, snp: 6, other: 0, total: 59 },
      { year: '2015',     con:  1, lab:  1, ld:  1, snp:56, other: 0, total: 59 },
      { year: '2017',     con: 13, lab:  7, ld:  4, snp:35, other: 0, total: 59 },
      { year: '2019',     con:  6, lab:  1, ld:  4, snp:48, other: 0, total: 59 },
      { year: '2024',     con:  5, lab: 37, ld:  6, snp: 9, other: 0, total: 57 },
    ],
    source: 'HC Library Research Briefing CBP-7529, UK Election Statistics 1918–2023',
  },
  'northern-ireland': {
    id: 'northern-ireland',
    name: 'Northern Ireland',
    constituencies: 18,
    electoralSystem: 'First Past the Post (Westminster); Single Transferable Vote (Assembly)',
    devolvedBody: 'Northern Ireland Assembly',
    devolvedYear: 1998,
    description: 'Northern Ireland returns 18 Westminster MPs. Its political landscape is distinct from the rest of the UK, structured around the constitutional question of unification with Ireland versus remaining in the United Kingdom. The Northern Ireland Assembly was established under the Good Friday Agreement of 1998 and uses the Single Transferable Vote system, electing 90 Members of the Legislative Assembly (MLAs) — 5 per constituency. The Executive requires cross-community support. In the 2022 Assembly election, Sinn Féin became the largest party for the first time since partition in 1922. Ulster Unionist MPs took the Conservative whip at Westminster until 1974. Sinn Féin MPs are elected but do not take their seats (abstentionism).',
    keyFacts: [
      'Northern Ireland Assembly established under the Good Friday Agreement, 1998',
      '90 MLAs elected by Single Transferable Vote (5 per constituency)',
      'Executive requires cross-community support — consociational democracy',
      'In 2022, Sinn Féin became the largest Assembly party for the first time since 1922',
      'Sinn Féin MPs are elected but do not take their seats at Westminster',
      'DUP replaced UUP as the largest unionist party in 2001',
      'Unionists had fewer Westminster seats than nationalists for the first time after 2019',
    ],
    assemblyResults: [
      { year: 1998, dup: 20, sf: 18, uup: 28, sdlp: 24, alliance: 6, others: 12 },
      { year: 2003, dup: 30, sf: 24, uup: 27, sdlp: 18, alliance: 6, others: 3 },
      { year: 2007, dup: 36, sf: 28, uup: 18, sdlp: 16, alliance: 7, others: 5 },
      { year: 2011, dup: 38, sf: 29, uup: 16, sdlp: 14, alliance: 8, others: 5 },
      { year: 2016, dup: 38, sf: 28, uup: 16, sdlp: 12, alliance: 8, others: 8 },
      { year: 2017, dup: 28, sf: 27, uup: 10, sdlp: 12, alliance: 8, others: 5 },
      { year: 2022, dup: 25, sf: 27, uup: 9, sdlp: 8, alliance: 17, others: 4 },
    ],
    westminsterEarly: [
      { year: '1922', unionist: 10, nationalist: 2, other: 0, total: 12 },
      { year: '1923', unionist: 10, nationalist: 2, other: 0, total: 12 },
      { year: '1924', unionist: 12, nationalist: 0, other: 0, total: 12 },
      { year: '1929', unionist: 10, nationalist: 2, other: 0, total: 12 },
      { year: '1931', unionist: 10, nationalist: 2, other: 0, total: 12 },
      { year: '1935', unionist: 10, nationalist: 2, other: 0, total: 12 },
      { year: '1945', unionist:  8, nationalist: 2, other: 2, total: 12 },
      { year: '1950', unionist: 10, nationalist: 2, other: 0, total: 12 },
      { year: '1951', unionist:  9, nationalist: 2, other: 1, total: 12 },
      { year: '1955', unionist: 10, nationalist: 0, other: 2, total: 12 },
      { year: '1959', unionist: 12, nationalist: 0, other: 0, total: 12 },
      { year: '1964', unionist: 12, nationalist: 0, other: 0, total: 12 },
      { year: '1966', unionist: 11, nationalist: 0, other: 1, total: 12 },
      { year: '1970', unionist:  8, nationalist: 0, other: 4, total: 12 },
    ],
    westminsterResults: [
      { year: 'Feb 1974', uup: 7, sdlp: 1, dup: 1, sf: 0, other: 3, total: 12 },
      { year: 'Oct 1974', uup: 6, sdlp: 1, dup: 1, sf: 0, other: 4, total: 12 },
      { year: '1979',     uup: 5, sdlp: 1, dup: 3, sf: 0, other: 3, total: 12 },
      { year: '1983',     uup:11, sdlp: 1, dup: 3, sf: 1, other: 1, total: 17 },
      { year: '1987',     uup: 9, sdlp: 3, dup: 3, sf: 1, other: 1, total: 17 },
      { year: '1992',     uup: 9, sdlp: 4, dup: 3, sf: 0, other: 1, total: 17 },
      { year: '1997',     uup:10, sdlp: 3, dup: 2, sf: 2, other: 1, total: 18 },
      { year: '2001',     uup: 6, sdlp: 3, dup: 5, sf: 4, other: 0, total: 18 },
      { year: '2005',     uup: 1, sdlp: 3, dup: 9, sf: 5, other: 0, total: 18 },
      { year: '2010',     uup: 0, sdlp: 3, dup: 8, sf: 5, other: 2, total: 18 },
      { year: '2015',     uup: 2, sdlp: 3, dup: 8, sf: 4, other: 1, total: 18 },
      { year: '2017',     uup: 0, sdlp: 0, dup:10, sf: 7, other: 1, total: 18 },
      { year: '2019',     uup: 0, sdlp: 2, dup: 8, sf: 7, other: 1, total: 18 },
      { year: '2024',     uup: 1, sdlp: 2, dup: 5, sf: 7, other: 3, total: 18 },
    ],
    source: 'HC Library Research Briefing CBP-7529, UK Election Statistics 1918–2023',
  },
  europe: {
    id: 'europe',
    name: 'Europe',
    constituencies: 73,
    electoralSystem: 'Regional list PR (GB) & STV (NI)',
    devolvedBody: 'European Parliament (UK seats)',
    devolvedYear: 1979,
    description: 'Pan-European political families and alliances that contested European Parliament elections in the United Kingdom from 1979 to 2019. UK parties sat in transnational groups — Socialists/PES/S&D, EPP-ED, ELDR/ALDE/Renew, Greens/EFA, and others — rather than as standalone national blocs. The UK held nine direct elections before leaving the EU; the final allocation in 2019 was 73 MEPs.',
    keyFacts: [
      'Nine direct European elections in the UK: 1979, 1984, 1989, 1994, 1999, 2004, 2009, 2014, and 2019',
      '73 UK MEPs at the final 2019 election (70 in Great Britain, 3 in Northern Ireland)',
      'Great Britain used FPTP (1979–1994) then regional list PR (1999–2019); Northern Ireland always used STV',
      'Labour MEPs sat in the Socialist/PES/S&D family throughout; Conservatives moved from EPP-ED to ECR in 2009',
      'Alliance manifestos on this site use 2019 group names; election pages show period-appropriate labels',
    ],
    source: 'European Parliament, Review of European and National Elections Results 2019; results.elections.europa.eu constitutive session data',
  },
};

/* ── Political spectrum order for parliament chart ─────────── */
const SPECTRUM_ORDER = [
  'sinnfein', 'workersparty', 'ssp', 'respect', 'tusc', 'communist', 'cpb', 'commonwealth', 'ilp', 'indlabour', 'sdlp',
  'irishnationalist', 'irishrepublican', 'antipartition', 'irishlabour', 'republicanlabour', 'unity',
  'plaid', 'green', 'walesgrn', 'scottishgrn', 'snp', 'labour', 'welshlab', 'scottishlab', 'alliance',
  'libdem', 'nationalliberal', 'natlibconservative', 'indliberal', 'welshlibdem', 'scottishlibdem',
  'national', 'nationalindependent', 'independent', 'indprogressive', 'speaker',
  'gpni', 'others', 'indconservative', 'uup', 'indunionist', 'ulsterpopularunionist', 'uuuc', 'ukup',
  'protestantunionist', 'vanguard', 'pup', 'dup', 'tuv', 'welshcon', 'scottishcon', 'conservative',
  'referendumparty', 'ukip', 'reform', 'bnp',
];

/* ── Election data ──────────────────────────────────────────── */
const ELECTIONS = [
  {
    id: '1945', year: 1945, displayYear: '1945', date: '5 July 1945',
    winner: 'labour', pm: 'Clement Attlee', outgoingPm: 'Winston Churchill',
    totalSeats: 640,
    summary: `The 1945 general election produced one of the most dramatic results in British political history. Despite Winston Churchill's enormous personal popularity as wartime leader, the electorate delivered a landslide victory to Clement Attlee's Labour Party. Labour won 393 seats — a majority of 146 — on a programme of postwar reconstruction, nationalisation, and the creation of a comprehensive welfare state.\n\nThe result shocked many observers, including Churchill himself. British voters distinguished between Churchill the war hero and the Conservative Party, whose pre-war record on unemployment and appeasement had not been forgotten. Labour's promise of a "New Jerusalem" — built on the wartime Beveridge Report's blueprint for a cradle-to-grave welfare state — resonated with a population exhausted by years of sacrifice and determined to avoid the poverty of the 1930s.\n\nThe Attlee government went on to create the National Health Service (1948), nationalise key industries including coal, steel, and the railways, and preside over Indian independence. It remains one of the most transformative governments in British history.`,
    highlights: [
      'Labour wins 393 seats — its greatest ever majority at the time',
      'Churchill loses despite leading Britain to victory in World War II',
      'Result attributed to working-class desire for postwar reform and memory of 1930s unemployment',
      'Attlee government goes on to create the NHS and nationalise key industries',
      'Three weeks between polling day (5 July) and result (26 July) — votes from soldiers abroad counted last',
    ],
    youtubeId: 'TZc3QHoALtU',
    extraManifestoParties: [],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  4, votes: 0, percentage: 23.8 },
      welshlab:    { party: 'welshlab',    seats: 25, votes: 0, percentage: 58.5 },
      welshlibdem: { party: 'welshlibdem', seats:  6, votes: 0, percentage: 14.9 },
      scottishcon: { party: 'scottishcon', seats: 27, votes: 0, percentage: 40.3 },
      scottishlab: { party: 'scottishlab', seats: 37, votes: 0, percentage: 47.9 },
      scottishlibdem: { party: 'scottishlibdem', seats:  0, votes: 0, percentage: 5.6 },
    },
    results: [
      { party: 'labour', seats: 393, votes: 11967746, percentage: 49.7  },
      { party: 'conservative', seats: 196, votes: 8699780, percentage: 36.1  },
      { party: 'libdem', seats:  12, votes: 2177938, percentage: 9  },
      { party: 'nationalliberal', seats:  11, votes: 686652, percentage: 2.9  },
      { party: 'independent', seats:   8, votes: 133191, percentage: 0.6  },
      { party: 'ilp', seats:   3, votes: 46769, percentage: 0.2  },
      { party: 'national', seats:   2, votes: 130513, percentage: 0.5  },
      { party: 'communist', seats:   2, votes: 97945, percentage: 0.4  },
      { party: 'irishnationalist', seats:   2, votes: 92819, percentage: 0.4  },
      { party: 'nationalindependent', seats:   2, votes: 65171, percentage: 0.3  },
      { party: 'indlabour', seats:   2, votes: 63135, percentage: 0.3  },
      { party: 'indconservative', seats:   2, votes: 57823, percentage: 0.2  },
      { party: 'indliberal', seats:   2, votes: 30450, percentage: 0.1  },
      { party: 'commonwealth', seats:   1, votes: 110634, percentage: 0.5  },
      { party: 'indprogressive', seats:   1, votes: 45967, percentage: 0.1  },
      { party: 'speaker', seats:   1, votes: 16431, percentage: 0.1  },
    ],
  },
  {
    id: '1950', year: 1950, displayYear: '1950', date: '23 February 1950',
    winner: 'labour', pm: 'Clement Attlee', outgoingPm: 'Clement Attlee',
    totalSeats: 625,
    summary: `Labour retained power in 1950 but with a drastically reduced majority of just 5 seats. The result reflected growing public ambivalence about the pace of nationalisation and the austerity of the postwar years, while the Conservatives had rebuilt under Churchill's continued leadership. New boundary changes disadvantaged Labour.`,
    highlights: [
      'Labour majority reduced to just 5 seats — barely workable',
      'Boundary changes disadvantage Labour in marginal seats',
      'Conservative Party revitalised under Churchill\'s continued leadership',
      'Korean War breaks out months later, complicating Attlee\'s government',
    ],
    youtubeId: 'QFUu9xbe18M',
    extraManifestoParties: [],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  4, votes: 0, percentage: 27.4 },
      welshlab:    { party: 'welshlab',    seats: 27, votes: 0, percentage: 58.1 },
      welshlibdem: { party: 'welshlibdem', seats:  5, votes: 0, percentage: 12.6 },
      scottishcon: { party: 'scottishcon', seats: 31, votes: 0, percentage: 44.8 },
      scottishlab: { party: 'scottishlab', seats: 37, votes: 0, percentage: 46.2 },
      scottishlibdem: { party: 'scottishlibdem', seats:  2, votes: 0, percentage: 6.6 },
    },
    results: [
      { party: 'labour', seats: 315, votes: 13266176, percentage: 46.1  },
      { party: 'conservative', seats: 277, votes: 11482357, percentage: 39.9  },
      { party: 'uup', seats:  10, votes: 352300, percentage: 1.2  },
      { party: 'libdem', seats:   9, votes: 2621487, percentage: 9.1  },
      { party: 'natlibconservative', seats:   9, votes: 815118, percentage: 2.8  },
      { party: 'nationalliberal', seats:   2, votes: 181137, percentage: 0.6  },
      { party: 'irishnationalist', seats:   2, votes: 65200, percentage: 0.2  },
      { party: 'speaker', seats:   1, votes: 24703, percentage: 0.1  },
    ],
  },
  {
    id: '1951', year: 1951, displayYear: '1951', date: '25 October 1951',
    winner: 'conservative', pm: 'Winston Churchill', outgoingPm: 'Clement Attlee',
    totalSeats: 625,
    summary: `The Conservatives won the 1951 election with a majority of 17 seats, returning Winston Churchill to Downing Street at the age of 76. Paradoxically, Labour won more votes than the Conservatives — 13.9 million to 13.7 million — making it one of the few British elections where the party winning fewer votes won more seats. The Liberal collapse left voters little choice but Conservative or Labour.`,
    highlights: [
      'Churchill returns to No. 10 at age 76',
      'Labour wins more votes than Conservatives but fewer seats',
      'Liberal Party collapses to just 6 MPs',
      'Beginning of 13 years of Conservative government (1951–1964)',
    ],
    youtubeId: 'P1415icoA2U',
    extraManifestoParties: [],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  6, votes: 0, percentage: 30.8 },
      welshlab:    { party: 'welshlab',    seats: 27, votes: 0, percentage: 60.5 },
      welshlibdem: { party: 'welshlibdem', seats:  3, votes: 0, percentage: 7.6 },
      scottishcon: { party: 'scottishcon', seats: 35, votes: 0, percentage: 48.6 },
      scottishlab: { party: 'scottishlab', seats: 35, votes: 0, percentage: 47.9 },
      scottishlibdem: { party: 'scottishlibdem', seats:  1, votes: 0, percentage: 2.7 },
    },
    results: [
      { party: 'conservative', seats: 297, votes: 12574037, percentage: 44.0  },
      { party: 'labour', seats: 295, votes: 13948605, percentage: 48.8  },
      { party: 'natlibconservative', seats:  14, votes: 986942, percentage: 3.5  },
      { party: 'uup', seats:   9, votes: 274900, percentage: 1.0  },
      { party: 'libdem', seats:   6, votes: 730546, percentage: 2.5  },
      { party: 'irishlabour', seats:   1, votes: 33714, percentage: 0.1  },
      { party: 'nationalliberal', seats:   1, votes: 70496, percentage: 0.2  },
      { party: 'antipartition', seats:   1, votes: 32717, percentage: 0.1  },
      { party: 'irishrepublican', seats:   1, votes: 33094, percentage: 0.1  },
    ],
  },
  {
    id: '1955', year: 1955, displayYear: '1955', date: '26 May 1955',
    winner: 'conservative', pm: 'Anthony Eden', outgoingPm: 'Winston Churchill',
    totalSeats: 630,
    summary: `Anthony Eden called and won a snap election shortly after succeeding Churchill as Prime Minister, increasing the Conservative majority to 60. Eden's personal popularity and economic stability helped secure the result. Labour under Hugh Gaitskell struggled to present a distinct alternative. Eden's triumph would be short-lived: the Suez Crisis of 1956 forced his resignation within two years.`,
    highlights: [
      'Eden increases Conservative majority to 60 seats',
      'First election fought with commercial television advertising',
      'Labour under Gaitskell cannot break through',
      'Suez Crisis would end Eden\'s premiership within 18 months',
    ],
    youtubeId: 'a23vcMCWWPA',
    extraManifestoParties: ['communist'],
    partyResults: {
      communist:   { party: 'communist',   seats:  0, votes: 33144, percentage: 0.1 },
      welshcon:    { party: 'welshcon',    seats:  6, votes: 0, percentage: 29.9 },
      welshlab:    { party: 'welshlab',    seats: 27, votes: 0, percentage: 57.6 },
      welshlibdem: { party: 'welshlibdem', seats:  3, votes: 0, percentage: 7.3 },
      scottishcon: { party: 'scottishcon', seats: 36, votes: 0, percentage: 50.1 },
      scottishlab: { party: 'scottishlab', seats: 34, votes: 0, percentage: 46.7 },
      scottishlibdem: { party: 'scottishlibdem', seats:  1, votes: 0, percentage: 1.9 },
    },
    results: [
      { party: 'conservative', seats: 319, votes: 12843969, percentage: 48.0  },
      { party: 'labour', seats: 277, votes: 12404970, percentage: 46.4  },
      { party: 'natlibconservative', seats:  13, votes: 0, percentage: 0  },
      { party: 'uup', seats:  10, votes: 442600, percentage: 1.7  },
      { party: 'libdem', seats:   6, votes: 722405, percentage: 2.7  },
      { party: 'sinnfein', seats:   2, votes: 168400, percentage: 0.6  },
      { party: 'nationalliberal', seats:   2, votes: 0, percentage: 0  },
      { party: 'speaker', seats:   1, votes: 25372, percentage: 0.1  },
    ],
  },
  {
    id: '1959', year: 1959, displayYear: '1959', date: '8 October 1959',
    winner: 'conservative', pm: 'Harold Macmillan', outgoingPm: 'Harold Macmillan',
    totalSeats: 630,
    summary: `Harold Macmillan led the Conservatives to their third consecutive election victory with a majority of 100. "Most of our people have never had it so good" captured the spirit of the age. Labour, divided over nuclear disarmament and Clause IV, could not capitalise on concerns about inequality.`,
    highlights: [
      '"Never had it so good" — rising prosperity favours the Conservatives',
      'First election heavily shaped by television campaigning',
      'Labour divided over nuclear disarmament (CND) and Clause IV',
      'Conservative majority of 100 — largest since 1935',
    ],
    youtubeId: 'bGhJr7V-M50',
    extraManifestoParties: [],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  7, votes: 0, percentage: 32.6 },
      welshlab:    { party: 'welshlab',    seats: 27, votes: 0, percentage: 56.4 },
      welshlibdem: { party: 'welshlibdem', seats:  2, votes: 0, percentage: 5.3 },
      scottishcon: { party: 'scottishcon', seats: 31, votes: 0, percentage: 47.2 },
      scottishlab: { party: 'scottishlab', seats: 38, votes: 0, percentage: 46.7 },
      scottishlibdem: { party: 'scottishlibdem', seats:  1, votes: 0, percentage: 4.1 },
    },
    results: [
      { party: 'conservative', seats: 342, votes: 13304830, percentage: 47.8  },
      { party: 'labour', seats: 258, votes: 12215538, percentage: 43.8  },
      { party: 'uup', seats:  12, votes: 445000, percentage: 1.6  },
      { party: 'natlibconservative', seats:  10, votes: 0, percentage: 0  },
      { party: 'libdem', seats:   6, votes: 1638571, percentage: 5.9  },
      { party: 'indunionist', seats:   1, votes: 12163, percentage: 0.0  },
      { party: 'nationalliberal', seats:   1, votes: 0, percentage: 0  },
    ],
  },
  {
    id: '1964', year: 1964, displayYear: '1964', date: '15 October 1964',
    winner: 'labour', pm: 'Harold Wilson', outgoingPm: 'Alec Douglas-Home',
    totalSeats: 630,
    summary: `Harold Wilson led Labour to a narrow victory after thirteen years of Conservative rule, winning a majority of just 4. Wilson, a moderniser who spoke of the "white heat of technology," tapped into a national mood for change. The Conservative government under Alec Douglas-Home appeared tired and out of touch.`,
    highlights: [
      'End of thirteen years of Conservative government',
      'Wilson\'s "white heat of technology" speech sets tone for modernising agenda',
      'Labour majority of only 4 — barely workable',
      'Profumo scandal had damaged the Conservatives in preceding years',
    ],
    youtubeId: 'QiUkyAS-fSs',
    extraManifestoParties: [],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  6, votes: 0, percentage: 29.4 },
      welshlab:    { party: 'welshlab',    seats: 28, votes: 0, percentage: 57.8 },
      welshlibdem: { party: 'welshlibdem', seats:  2, votes: 0, percentage: 7.3 },
      scottishcon: { party: 'scottishcon', seats: 24, votes: 0, percentage: 40.6 },
      scottishlab: { party: 'scottishlab', seats: 43, votes: 0, percentage: 48.7 },
      scottishlibdem: { party: 'scottishlibdem', seats:  4, votes: 0, percentage: 7.6 },
    },
    results: [
      { party: 'labour', seats: 317, votes: 12205814, percentage: 44.1  },
      { party: 'conservative', seats: 291, votes: 11577908, percentage: 41.9  },
      { party: 'uup', seats:  12, votes: 401900, percentage: 1.5  },
      { party: 'libdem', seats:   9, votes: 3092878, percentage: 11.2  },
      { party: 'speaker', seats:   1, votes: 21588, percentage: 0.1  },
    ],
  },
  {
    id: '1966', year: 1966, displayYear: '1966', date: '31 March 1966',
    winner: 'labour', pm: 'Harold Wilson', outgoingPm: 'Harold Wilson',
    totalSeats: 630,
    summary: `Wilson called a snap election to strengthen his tiny majority and won decisively, giving Labour 363 seats and a majority of 96. The result gave Wilson a mandate to pursue his modernisation agenda. However, sterling devaluation and industrial unrest would soon undermine his second administration.`,
    highlights: [
      'Wilson wins decisive mandate; Labour majority increases to 96',
      'England hosts and wins the FIFA World Cup later that year',
      'Sterling devaluation crisis would later embarrass Wilson\'s government',
    ],
    youtubeId: '6lBbSSIv9Ww',
    extraManifestoParties: ['communist'],
    partyResults: {
      communist:   { party: 'communist',   seats:  0, votes: 62092, percentage: 0.2 },
      welshcon:    { party: 'welshcon',    seats:  3, votes: 0, percentage: 27.9 },
      welshlab:    { party: 'welshlab',    seats: 32, votes: 0, percentage: 60.7 },
      welshlibdem: { party: 'welshlibdem', seats:  1, votes: 0, percentage: 6.3 },
      scottishcon: { party: 'scottishcon', seats: 20, votes: 0, percentage: 37.6 },
      scottishlab: { party: 'scottishlab', seats: 46, votes: 0, percentage: 49.9 },
      scottishlibdem: { party: 'scottishlibdem', seats:  5, votes: 0, percentage: 6.8 },
    },
    results: [
      { party: 'labour', seats: 363, votes: 13064951, percentage: 47.9  },
      { party: 'conservative', seats: 241, votes: 11049833, percentage: 40.5  },
      { party: 'libdem', seats:  12, votes: 2327533, percentage: 8.5  },
      { party: 'uup', seats:  11, votes: 368600, percentage: 1.4  },
      { party: 'republicanlabour', seats:   1, votes: 26292, percentage: 0.1  },
      { party: 'natlibconservative', seats:   1, votes: 0, percentage: 0  },
      { party: 'speaker', seats:   1, votes: 30463, percentage: 0.1  },
    ],
  },
  {
    id: '1970', year: 1970, displayYear: '1970', date: '18 June 1970',
    winner: 'conservative', pm: 'Edward Heath', outgoingPm: 'Harold Wilson',
    totalSeats: 630,
    summary: `The 1970 election produced one of the great upsets in British electoral history. Opinion polls had consistently shown Labour ahead, but Edward Heath's Conservatives won a comfortable majority of 30. Heath's government would go on to take the UK into the European Economic Community in 1973 but struggle with industrial unrest, power cuts, and the three-day week.`,
    highlights: [
      'Major polling upset — Conservatives win despite trailing in surveys',
      'Heath takes UK into the European Economic Community in 1973',
      'First election in which 18-year-olds could vote',
      'Enoch Powell\'s "Rivers of Blood" speech had influenced the political mood',
    ],
    youtubeId: 'cq8PMfpA-6g',
    extraManifestoParties: [],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  7, votes: 0, percentage: 27.7 },
      welshlab:    { party: 'welshlab',    seats: 27, votes: 0, percentage: 51.6 },
      welshlibdem: { party: 'welshlibdem', seats:  1, votes: 0, percentage: 6.8 },
      scottishcon: { party: 'scottishcon', seats: 23, votes: 0, percentage: 38.0 },
      scottishlab: { party: 'scottishlab', seats: 44, votes: 0, percentage: 44.5 },
      scottishlibdem: { party: 'scottishlibdem', seats:  3, votes: 0, percentage: 5.5 },
    },
    results: [
      { party: 'conservative', seats: 322, votes: 12723123, percentage: 44.9  },
      { party: 'labour', seats: 287, votes: 12175174, percentage: 43.1  },
      { party: 'uup', seats:   8, votes: 422000, percentage: 1.5  },
      { party: 'libdem', seats:   6, votes: 2030611, percentage: 7.2  },
      { party: 'unity', seats:   2, votes: 71521, percentage: 0.3  },
      { party: 'protestantunionist', seats:   1, votes: 24130, percentage: 0.1  },
      { party: 'republicanlabour', seats:   1, votes: 30649, percentage: 0.1  },
      { party: 'indlabour', seats:   1, votes: 16701, percentage: 0.1  },
      { party: 'speaker', seats:   1, votes: 29417, percentage: 0.1  },
      { party: 'snp', seats:   1, votes: 306800, percentage: 1.1  },
    ],
  },
  {
    id: 'feb1974', year: 1974, displayYear: 'Feb 1974', date: '28 February 1974',
    winner: 'labour', pm: 'Harold Wilson', outgoingPm: 'Edward Heath',
    totalSeats: 635,
    summary: `Edward Heath called this election against the backdrop of the miners' strike and the three-day working week, posing the question "Who governs Britain?" The answer was a hung parliament — the first since 1929. Labour won the most seats (301) but not a majority. Heath attempted to form a coalition with the Liberals but negotiations failed. Wilson returned to Downing Street leading a minority government.\n\nNote: Ulster Unionist MPs had previously taken the Conservative whip at Westminster, but following the Sunningdale Agreement dispute the whip was removed in 1974. UUP seats are listed separately from this election onwards.`,
    highlights: [
      'Hung parliament — first since 1929',
      'Heath\'s "Who governs Britain?" election backfires',
      'Miners\' strike and three-day week dominate campaign',
      'Liberal Party wins 14 seats and 19.3% of the vote',
      'UUP breaks from Conservative whip — listed separately from this election',
    ],
    youtubeId: 'Tcw05fhSyQg',
    extraManifestoParties: [],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  8, votes: 0, percentage: 25.9 },
      welshlab:    { party: 'welshlab',    seats: 24, votes: 0, percentage: 46.8 },
      welshlibdem: { party: 'welshlibdem', seats:  2, votes: 0, percentage: 16.0 },
      scottishcon: { party: 'scottishcon', seats: 21, votes: 0, percentage: 32.9 },
      scottishlab: { party: 'scottishlab', seats: 40, votes: 0, percentage: 36.6 },
      scottishlibdem: { party: 'scottishlibdem', seats:  3, votes: 0, percentage: 7.9 },
    },
    results: [
      { party: 'labour', seats: 301, votes: 11607044, percentage: 37.2  },
      { party: 'conservative', seats: 296, votes: 11902195, percentage: 37.9  },
      { party: 'libdem', seats:  15, votes: 6042771, percentage: 19.3  },
      { party: 'snp', seats:   7, votes: 633200, percentage: 2.0  },
      { party: 'uup', seats:   7, votes: 326400, percentage: 1.0  },
      { party: 'vanguard', seats:   3, votes: 172100, percentage: 0.5  },
      { party: 'plaid', seats:   2, votes: 171400, percentage: 0.5  },
      { party: 'sdlp', seats:   1, votes: 160400, percentage: 0.5  },
      { party: 'dup', seats:   1, votes: 58700, percentage: 0.2  },
      { party: 'speaker', seats:   1, votes: 38452, percentage: 0.1  },
      { party: 'indlabour', seats:   1, votes: 22918, percentage: 0.1  },
    ],
  },
  {
    id: 'oct1974', year: 1974, displayYear: 'Oct 1974', date: '10 October 1974',
    winner: 'labour', pm: 'Harold Wilson', outgoingPm: 'Harold Wilson',
    totalSeats: 635,
    summary: `Wilson called a second election within the year to convert his minority government into a workable majority. He succeeded, but only barely — Labour won 319 seats, giving a majority of just 3. This slim margin would erode through by-election losses, leaving Labour in minority government again by 1977.`,
    highlights: [
      'Labour secures working majority of 3 — barely sufficient',
      'SNP wins 11 seats, capitalising on North Sea oil debate',
      'Liberal vote squeezed by voters wanting a decisive result',
      'Margaret Thatcher wins Conservative leadership in February 1975',
    ],
    youtubeId: 'oGlLs2fpLk0',
    extraManifestoParties: [],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  8, votes: 0, percentage: 23.9 },
      welshlab:    { party: 'welshlab',    seats: 23, votes: 0, percentage: 49.5 },
      welshlibdem: { party: 'welshlibdem', seats:  2, votes: 0, percentage: 15.5 },
      scottishcon: { party: 'scottishcon', seats: 16, votes: 0, percentage: 24.7 },
      scottishlab: { party: 'scottishlab', seats: 41, votes: 0, percentage: 36.3 },
      scottishlibdem: { party: 'scottishlibdem', seats:  3, votes: 0, percentage: 8.3 },
    },
    results: [
      { party: 'labour', seats: 319, votes: 11431491, percentage: 39.2  },
      { party: 'conservative', seats: 276, votes: 10213151, percentage: 35.0  },
      { party: 'libdem', seats:  13, votes: 5030173, percentage: 18.3  },
      { party: 'snp', seats:  11, votes: 839600, percentage: 2.9  },
      { party: 'uup', seats:   6, votes: 256100, percentage: 0.9  },
      { party: 'plaid', seats:   3, votes: 166300, percentage: 0.6  },
      { party: 'vanguard', seats:   3, votes: 126598, percentage: 0.4  },
      { party: 'sdlp', seats:   1, votes: 154200, percentage: 0.5  },
      { party: 'dup', seats:   1, votes: 59500, percentage: 0.2  },
      { party: 'speaker', seats:   1, votes: 35705, percentage: 0.1  },
      { party: 'independent', seats:   1, votes: 32980, percentage: 0.1  },
    ],
  },
  {
    id: '1979', year: 1979, displayYear: '1979', date: '3 May 1979',
    winner: 'conservative', pm: 'Margaret Thatcher', outgoingPm: 'James Callaghan',
    totalSeats: 635,
    summary: `The 1979 election brought Margaret Thatcher to power and ushered in one of the most ideologically transformative governments of the twentieth century. Labour under James Callaghan had survived the "Winter of Discontent" (1978–79) but could not escape the damage to its reputation. Callaghan fell after losing a vote of no confidence by a single vote. Thatcher won a majority of 43, becoming the first female Prime Minister in British history.`,
    highlights: [
      'Margaret Thatcher becomes Britain\'s first female Prime Minister',
      'Callaghan government falls on vote of no confidence — by one vote',
      '"Winter of Discontent" shapes the election narrative',
      'Saatchi & Saatchi\'s "Labour Isn\'t Working" poster becomes iconic',
      'Beginning of 18 years of Conservative government (1979–1997)',
    ],
    youtubeId: 'MjBTSjG-zuY',
    extraManifestoParties: ['green'],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats: 11, votes: 0, percentage: 32.2 },
      welshlab:    { party: 'welshlab',    seats: 22, votes: 0, percentage: 48.6 },
      welshlibdem: { party: 'welshlibdem', seats:  1, votes: 0, percentage: 10.6 },
      scottishcon: { party: 'scottishcon', seats: 22, votes: 0, percentage: 31.4 },
      scottishlab: { party: 'scottishlab', seats: 44, votes: 0, percentage: 41.5 },
      scottishlibdem: { party: 'scottishlibdem', seats:  3, votes: 0, percentage: 9.0 },
    },
    results: [
      { party: 'conservative', seats: 339, votes: 13069731, percentage: 43.9  },
      { party: 'labour', seats: 268, votes: 11505883, percentage: 36.9  },
      { party: 'libdem', seats:  11, votes: 4285761, percentage: 13.8  },
      { party: 'uup', seats:   6, votes: 254600, percentage: 0.8  },
      { party: 'dup', seats:   3, votes: 71000, percentage: 0.2  },
      { party: 'plaid', seats:   2, votes: 132500, percentage: 0.4  },
      { party: 'snp', seats:   2, votes: 504300, percentage: 1.6  },
      { party: 'sdlp', seats:   1, votes: 126300, percentage: 0.4  },
      { party: 'speaker', seats:   1, votes: 27035, percentage: 0.1  },
      { party: 'independent', seats:   1, votes: 22398, percentage: 0.1  },
      { party: 'uuuc', seats:   1, votes: 29249, percentage: 0.1  },
    ],
  },
  {
    id: '1983', year: 1983, displayYear: '1983', date: '9 June 1983',
    winner: 'conservative', pm: 'Margaret Thatcher', outgoingPm: 'Margaret Thatcher',
    totalSeats: 650,
    summary: `Thatcher won a landslide majority of 144 seats — the largest since 1945 — buoyed by the "Falklands Factor." Labour, under Michael Foot, campaigned on a left-wing manifesto described by Gerald Kaufman as "the longest suicide note in history." The SDP–Liberal Alliance won 25.4% of the vote — only just below Labour's 27.6% — but won only 23 seats under first-past-the-post.`,
    highlights: [
      'Falklands Factor delivers Thatcher a majority of 144',
      'Labour\'s manifesto dubbed "the longest suicide note in history"',
      'SDP–Liberal Alliance wins 25.4% of votes but only 23 seats',
      'Neil Kinnock begins rebuilding Labour in the years following',
    ],
    youtubeId: 'AZm_TTa8wcI',
    extraManifestoParties: ['green', 'scottishcon', 'welshcon'],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats: 14, votes: 0, percentage: 31.0 },
      welshlab:    { party: 'welshlab',    seats: 20, votes: 0, percentage: 37.5 },
      welshlibdem: { party: 'welshlibdem', seats:  2, votes: 0, percentage: 23.2 },
      scottishcon: { party: 'scottishcon', seats: 21, votes: 0, percentage: 28.4 },
      scottishlab: { party: 'scottishlab', seats: 41, votes: 0, percentage: 35.1 },
      scottishlibdem: { party: 'scottishlibdem', seats:  8, votes: 0, percentage: 24.5 },
    },
    results: [
      { party: 'conservative', seats: 397, votes: 13012316, percentage: 42.4  },
      { party: 'labour', seats: 209, votes: 8271837, percentage: 27.6  },
      { party: 'libdem', seats:  23, votes: 7780486, percentage: 25.4  },
      { party: 'uup', seats:  11, votes: 260000, percentage: 0.8  },
      { party: 'dup', seats:   3, votes: 152700, percentage: 0.5  },
      { party: 'plaid', seats:   2, votes: 125300, percentage: 0.4  },
      { party: 'snp', seats:   2, votes: 332000, percentage: 1.1  },
      { party: 'sinnfein', seats:   1, votes: 102700, percentage: 0.3  },
      { party: 'ulsterpopularunionist', seats:   1, votes: 22861, percentage: 0.1  },
      { party: 'sdlp', seats:   1, votes: 137000, percentage: 0.4  },
    ],
  },
  {
    id: '1987', year: 1987, displayYear: '1987', date: '11 June 1987',
    winner: 'conservative', pm: 'Margaret Thatcher', outgoingPm: 'Margaret Thatcher',
    totalSeats: 650,
    summary: `Thatcher won her third consecutive victory with a majority of 102. Despite unemployment and bitter divisions over the miners' strike, Labour under Neil Kinnock still could not break through. Thatcher's third term would be marked by the introduction of the poll tax, which triggered mass protests and ultimately contributed to her downfall in 1990.`,
    highlights: [
      'Thatcher wins historic third consecutive term',
      'Labour still cannot overcome "unelectability" reputation despite Kinnock\'s reforms',
      'Poll tax announced in manifesto — would prove politically fatal',
      'Peter Mandelson\'s slick Labour campaign sets template for future professionalism',
    ],
    youtubeId: 'bVahD8xWoxo',
    youtubeStart: 22,
    extraManifestoParties: ['green'],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  8, votes: 0, percentage: 29.5 },
      welshlab:    { party: 'welshlab',    seats: 24, votes: 0, percentage: 45.1 },
      welshlibdem: { party: 'welshlibdem', seats:  3, votes: 0, percentage: 17.9 },
      scottishcon: { party: 'scottishcon', seats: 10, votes: 0, percentage: 24.0 },
      scottishlab: { party: 'scottishlab', seats: 50, votes: 0, percentage: 42.4 },
      scottishlibdem: { party: 'scottishlibdem', seats:  9, votes: 0, percentage: 19.2 },
    },
    results: [
      { party: 'conservative', seats: 375, votes: 13736747, percentage: 42.2  },
      { party: 'labour', seats: 229, votes: 10029027, percentage: 30.8  },
      { party: 'libdem', seats:  22, votes: 7341291, percentage: 22.6  },
      { party: 'uup', seats:   9, votes: 276200, percentage: 0.8  },
      { party: 'snp', seats:   3, votes: 416500, percentage: 1.3  },
      { party: 'dup', seats:   3, votes: 85600, percentage: 0.3  },
      { party: 'plaid', seats:   3, votes: 123600, percentage: 0.4  },
      { party: 'sdlp', seats:   3, votes: 154100, percentage: 0.5  },
      { party: 'sinnfein', seats:   1, votes: 83400, percentage: 0.3  },
      { party: 'speaker', seats:   1, votes: 24188, percentage: 0.1  },
      { party: 'ulsterpopularunionist', seats:   1, votes: 18420, percentage: 0.1  },
    ],
  },
  {
    id: '1992', year: 1992, displayYear: '1992', date: '9 April 1992',
    winner: 'conservative', pm: 'John Major', outgoingPm: 'John Major',
    totalSeats: 651,
    summary: `The 1992 election produced another major polling failure. John Major's Conservatives won 14.1 million votes — the highest total ever cast for a single party in British history. Labour under Neil Kinnock suffered a fourth consecutive defeat. "It's the Sun wot won it," claimed Rupert Murdoch's newspaper. "Black Wednesday" in September would destroy Conservative economic credibility.`,
    highlights: [
      'Major wins record 14.1 million votes — highest for any party in British history',
      'Fourth consecutive Labour defeat despite confident polling predictions',
      '"Kinnock\'s Sheffield rally" becomes byword for overconfidence',
      '"Black Wednesday" ERM crisis follows in September, destroying Conservative economic credibility',
      'Neil Kinnock resigns; John Smith and then Tony Blair reshape the party',
    ],
    youtubeId: 'rXAwSquD4ZU',
    extraManifestoParties: ['green', 'bnp'],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  6, votes: 0, percentage: 28.6 },
      welshlab:    { party: 'welshlab',    seats: 27, votes: 0, percentage: 49.5 },
      welshlibdem: { party: 'welshlibdem', seats:  1, votes: 0, percentage: 12.4 },
      scottishcon: { party: 'scottishcon', seats: 11, votes: 0, percentage: 25.6 },
      scottishlab: { party: 'scottishlab', seats: 49, votes: 0, percentage: 39.0 },
      scottishlibdem: { party: 'scottishlibdem', seats:  9, votes: 0, percentage: 13.1 },
    },
    results: [
      { party: 'conservative', seats: 336, votes: 14093007, percentage: 41.9  },
      { party: 'labour', seats: 271, votes: 11624109, percentage: 34.4  },
      { party: 'libdem', seats:  20, votes: 5990604, percentage: 17.8  },
      { party: 'uup', seats:   9, votes: 271000, percentage: 0.8  },
      { party: 'sdlp', seats:   4, votes: 154400, percentage: 0.5  },
      { party: 'plaid', seats:   4, votes: 154900, percentage: 0.5  },
      { party: 'snp', seats:   3, votes: 629600, percentage: 1.9  },
      { party: 'dup', seats:   3, votes: 103000, percentage: 0.3  },
      { party: 'ulsterpopularunionist', seats:   1, votes: 19305, percentage: 0.1  },
    ],
  },
  {
    id: '1997', year: 1997, displayYear: '1997', date: '1 May 1997',
    winner: 'labour', pm: 'Tony Blair', outgoingPm: 'John Major',
    totalSeats: 659,
    summary: `Tony Blair's Labour swept to a landslide majority of 179 seats — the largest in Labour history — after eighteen years in opposition. "Things can only get better" became the anthem of a party transformed into "New Labour": fiscally responsible, media-savvy, occupying the centre ground. Many previously safe Conservative seats in the south fell for the first time. Blair's victory represented a seismic realignment of British politics.`,
    highlights: [
      'Labour wins 179-seat majority — greatest in Labour history',
      '"Things Can Only Get Better" by D:Ream becomes defining anthem',
      'Eighteen years of Conservative rule ends in one night',
      '"Portillo moment" — Defence Secretary loses his seat live on television',
      'Good Friday Agreement signed in Northern Ireland the following year',
      'The Referendum Party won over 800,000 votes on an EU referendum platform',
    ],
    youtubeId: 'XoL_tT046tI',
    extraManifestoParties: ['pup', 'niwc', 'referendumparty', 'ukip', 'alliance', 'scottishlibdem'],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  0, votes: 0, percentage: 19.6 },
      welshlab:    { party: 'welshlab',    seats: 34, votes: 0, percentage: 54.7 },
      welshlibdem: { party: 'welshlibdem', seats:  2, votes: 0, percentage: 12.3 },
      scottishcon: { party: 'scottishcon', seats:  0, votes: 0, percentage: 17.5 },
      scottishlab: { party: 'scottishlab', seats: 56, votes: 0, percentage: 45.6 },
      scottishlibdem: { party: 'scottishlibdem', seats: 10, votes: 0, percentage: 13.0 },
    },
    results: [
      { party: 'labour', seats: 418, votes: 16661454, percentage: 43.2  },
      { party: 'conservative', seats: 165, votes: 9571673, percentage: 30.7  },
      { party: 'libdem', seats:  46, votes: 5181677, percentage: 16.8  },
      { party: 'uup', seats:  10, votes: 258300, percentage: 0.8  },
      { party: 'snp', seats:   6, votes: 621600, percentage: 2.0  },
      { party: 'plaid', seats:   4, votes: 161000, percentage: 0.5  },
      { party: 'sdlp', seats:   3, votes: 190800, percentage: 0.6  },
      { party: 'sinnfein', seats:   2, votes: 126900, percentage: 0.4  },
      { party: 'dup', seats:   2, votes: 107300, percentage: 0.3  },
      { party: 'ukup', seats:   1, votes: 107300, percentage: 0.3  },
      { party: 'independent', seats:   1, votes: 29354, percentage: 0.1  },
      { party: 'speaker', seats:   1, votes: 23969, percentage: 0.1  },
    ],
  },
  {
    id: '2001', year: 2001, displayYear: '2001', date: '7 June 2001',
    winner: 'labour', pm: 'Tony Blair', outgoingPm: 'Tony Blair',
    totalSeats: 659,
    summary: `Labour won a second consecutive landslide, with Blair becoming the first Labour leader to serve two full terms as Prime Minister. Record low turnout at 59.4% reflected widespread satisfaction but also disengagement. Blair's second term would be defined by the invasion of Iraq in 2003, which deeply divided the country and from which Blair's reputation never fully recovered.`,
    highlights: [
      'Labour wins second consecutive landslide — a first in party history',
      'Conservative Hague resigns after failing to make inroads',
      'Record low turnout: 59.4%',
      'Iraq War in 2003 would later dominate Blair\'s legacy',
      'Lib Dems advance to 52 seats under Charles Kennedy',
    ],
    youtubeId: '-HGDplurdMQ',
    extraManifestoParties: ['ukip', 'green', 'welshlab', 'welshlibdem', 'scottishcon', 'scottishlab', 'omrlp', 'stuckist'],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  0, votes: 0, percentage: 19.6 },
      welshlab:    { party: 'welshlab',    seats: 34, votes: 0, percentage: 48.6 },
      welshlibdem: { party: 'welshlibdem', seats:  2, votes: 0, percentage: 13.8 },
      scottishcon: { party: 'scottishcon', seats:  1, votes: 0, percentage: 15.6 },
      scottishlab: { party: 'scottishlab', seats: 55, votes: 0, percentage: 43.3 },
      scottishlibdem: { party: 'scottishlibdem', seats: 10, votes: 0, percentage: 16.3 },
    },
    results: [
      { party: 'labour', seats: 412, votes: 10834800, percentage: 40.7  },
      { party: 'conservative', seats: 166, votes: 8355683, percentage: 31.7  },
      { party: 'libdem', seats:  52, votes: 4840340, percentage: 18.3  },
      { party: 'uup', seats:   6, votes: 216800, percentage: 0.8  },
      { party: 'snp', seats:   5, votes: 464300, percentage: 1.8  },
      { party: 'dup', seats:   5, votes: 182000, percentage: 0.7  },
      { party: 'sinnfein', seats:   4, votes: 175900, percentage: 0.7  },
      { party: 'plaid', seats:   4, votes: 195900, percentage: 0.7  },
      { party: 'sdlp', seats:   3, votes: 169900, percentage: 0.6  },
      { party: 'speaker', seats:   1, votes: 16053, percentage: 0.1  },
      { party: 'others', seats:   1, votes: 28487, percentage: 0.1  },
    ],
  },
  {
    id: '2005', year: 2005, displayYear: '2005', date: '5 May 2005',
    winner: 'labour', pm: 'Tony Blair', outgoingPm: 'Tony Blair',
    totalSeats: 646,
    summary: `Labour won a reduced but still comfortable majority of 66, becoming the first Labour government to win three consecutive terms. However, the Iraq War had severely damaged Blair's authority — Labour's vote share fell from 40.7% to 35.2%, and the party lost 47 seats. The Liberal Democrats, strongly anti-war under Charles Kennedy, advanced to 62 seats — their best result in modern times.`,
    highlights: [
      'Labour wins historic third consecutive term',
      'Iraq War damages Blair\'s vote share significantly',
      'Liberal Democrats advance to 62 seats on anti-war platform',
      'Blair announces he will not serve full term; Brown transition begins',
      'Lowest Labour vote share since 1987 despite majority win',
    ],
    youtubeId: '-fz6OdDZhT0',
    extraManifestoParties: ['cooperative', 'ukip', 'bnp', 'respect', 'ssp', 'alliance', 'green', 'welshcon', 'scottishgrn', 'welshlab', 'welshlibdem', 'scottishcon', 'scottishlab', 'scottishlibdem', 'omrlp', 'cpa', 'englishdemocrats', 'forwardwales', 'sea', 'veritas', 'socialistlabour'],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  3, votes: 0, percentage: 21.4 },
      welshlab:    { party: 'welshlab',    seats: 29, votes: 0, percentage: 42.7 },
      welshlibdem: { party: 'welshlibdem', seats:  4, votes: 0, percentage: 18.4 },
      scottishcon: { party: 'scottishcon', seats:  1, votes: 0, percentage: 15.8 },
      scottishlab: { party: 'scottishlab', seats: 40, votes: 0, percentage: 38.9 },
      scottishlibdem: { party: 'scottishlibdem', seats: 11, votes: 0, percentage: 22.6 },
    },
    results: [
      { party: 'labour', seats: 355, votes: 9552589, percentage: 35.2  },
      { party: 'conservative', seats: 199, votes: 8782966, percentage: 32.4  },
      { party: 'libdem', seats:  62, votes: 5961718, percentage: 22  },
      { party: 'dup', seats:   9, votes: 241900, percentage: 0.9  },
      { party: 'snp', seats:   6, votes: 412300, percentage: 1.5  },
      { party: 'sinnfein', seats:   5, votes: 174500, percentage: 0.6  },
      { party: 'sdlp', seats:   3, votes: 125600, percentage: 0.5  },
      { party: 'plaid', seats:   3, votes: 174800, percentage: 0.6  },
      { party: 'respect', seats:   1, votes: 15891, percentage: 0.1  },
      { party: 'independent', seats:   1, votes: 20505, percentage: 0.1  },
      { party: 'uup', seats:   1, votes: 127400, percentage: 0.5  },
      { party: 'speaker', seats:   1, votes: 15153, percentage: 0.1  },
    ],
  },
  {
    id: '2010', year: 2010, displayYear: '2010', date: '6 May 2010',
    winner: 'conservative', pm: 'David Cameron', outgoingPm: 'Gordon Brown',
    totalSeats: 650,
    summary: `The 2010 election produced Britain's first hung parliament since February 1974. Gordon Brown's Labour, battered by the 2008 global financial crisis, lost 91 seats. David Cameron's Conservatives fell 20 seats short of an outright majority. After five days of negotiation, the Conservatives and Liberal Democrats formed a formal Coalition Government — the first peacetime coalition since the 1930s. Nick Clegg became Deputy Prime Minister.`,
    highlights: [
      'First hung parliament since February 1974',
      'Cleggmania — Lib Dem surge in polls after first-ever televised leaders\' debates',
      'Conservative–Liberal Democrat Coalition formed after five days of negotiations',
      'First peacetime coalition government since the 1930s',
      'Gordon Brown resigns from Downing Street in televised address',
    ],
    supplementaryDocuments: [
      {
        title: 'Conservative–Liberal Democrat coalition agreement',
        pdf: '/documents/supplementary/westminster/2010/coalition-programme-for-government.pdf',
      },
    ],
    youtubeId: 'R9emO6B8HFE',
    extraManifestoParties: ['cooperative', 'gpni', 'ukip', 'bnp', 'uup', 'tuv', 'pirate', 'welshcon', 'scottishgrn', 'welshlab', 'welshlibdem', 'scottishcon', 'scottishlab', 'scottishlibdem'],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  8, votes: 0, percentage: 26.1 },
      welshlab:    { party: 'welshlab',    seats: 26, votes: 0, percentage: 36.2 },
      welshlibdem: { party: 'welshlibdem', seats:  3, votes: 0, percentage: 20.1 },
      scottishcon: { party: 'scottishcon', seats:  1, votes: 0, percentage: 16.7 },
      scottishlab: { party: 'scottishlab', seats: 41, votes: 0, percentage: 42.0 },
      scottishlibdem: { party: 'scottishlibdem', seats: 11, votes: 0, percentage: 18.9 },
    },
    results: [
      { party: 'conservative', seats: 306, votes: 10703654, percentage: 36.1  },
      { party: 'labour', seats: 258, votes: 8606517, percentage: 29.0  },
      { party: 'libdem', seats:  57, votes: 6836248, percentage: 23.0  },
      { party: 'dup', seats:   8, votes: 168216, percentage: 0.6  },
      { party: 'snp', seats:   6, votes: 491386, percentage: 1.7  },
      { party: 'sinnfein', seats:   5, votes: 171942, percentage: 0.6  },
      { party: 'sdlp', seats:   3, votes: 110970, percentage: 0.4  },
      { party: 'plaid', seats:   3, votes: 165394, percentage: 0.6  },
      { party: 'alliance', seats:   1, votes: 42762, percentage: 0.1  },
      { party: 'green', seats:   1, votes: 265243, percentage: 0.9  },
      { party: 'speaker', seats:   1, votes: 22860, percentage: 0.1  },
      { party: 'independent', seats:   1, votes: 21181, percentage: 0.1  },
    ],
  },
  {
    id: '2015', year: 2015, displayYear: '2015', date: '7 May 2015',
    winner: 'conservative', pm: 'David Cameron', outgoingPm: 'David Cameron',
    totalSeats: 650,
    summary: `The 2015 election delivered the second major polling failure of the modern era. Surveys had predicted another hung parliament; instead Cameron won an outright majority of 12. Labour's Ed Miliband lost 26 seats. Most dramatically, the SNP swept Scotland, winning 56 of 59 Scottish seats and virtually wiping out Scottish Labour. The Liberal Democrats were decimated, falling from 57 to 8 seats. UKIP won nearly 4 million votes but only 1 seat. Cameron's victory came with a manifesto commitment to an EU membership referendum.`,
    highlights: [
      'Major polling failure — predicted hung parliament becomes Conservative majority',
      'SNP sweeps Scotland, winning 56 of 59 seats — "SNP tsunami"',
      'Liberal Democrats punished for coalition — fall from 57 to 8 seats',
      'UKIP wins 3.9 million votes (12.6%) but only 1 seat',
      'Cameron commits to EU referendum; Brexit vote follows in 2016',
      'Miliband resigns; Jeremy Corbyn elected Labour leader months later',
    ],
    youtubeId: 'VjJDyIAI4SI',
    extraManifestoParties: ['cooperative', 'gpni', 'pirate', 'tuv', 'welshcon', 'scottishgrn', 'welshlab', 'welshlibdem', 'scottishcon', 'scottishlab', 'scottishlibdem', 'omrlp', 'animalpolitics', 'nicon', 'nha', 'ssp', 'socialistalternative', 'tusc', 'workerspartyie', 'alliance', 'socialistlabour', 'cista'],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats: 11, votes: 0, percentage: 27.2 },
      welshlab:    { party: 'welshlab',    seats: 25, votes: 0, percentage: 36.9 },
      welshlibdem: { party: 'welshlibdem', seats:  1, votes: 0, percentage: 6.5 },
      scottishcon: { party: 'scottishcon', seats:  1, votes: 0, percentage: 14.9 },
      scottishlab: { party: 'scottishlab', seats:  1, votes: 0, percentage: 24.3 },
      scottishlibdem: { party: 'scottishlibdem', seats:  1, votes: 0, percentage: 7.5 },
    },
    results: [
      { party: 'conservative', seats: 330, votes: 11299609, percentage: 36.8  },
      { party: 'labour', seats: 232, votes: 9347273, percentage: 30.4  },
      { party: 'snp', seats:  56, votes: 1454436, percentage: 4.7  },
      { party: 'dup', seats:   8, votes: 184260, percentage: 0.6  },
      { party: 'libdem', seats:   8, votes: 2415916, percentage: 7.9  },
      { party: 'sinnfein', seats:   4, votes: 176232, percentage: 0.6  },
      { party: 'plaid', seats:   3, votes: 181704, percentage: 0.6  },
      { party: 'sdlp', seats:   3, votes: 99809, percentage: 0.3  },
      { party: 'uup', seats:   2, votes: 114935, percentage: 0.4  },
      { party: 'green', seats:   1, votes: 1111603, percentage: 3.6  },
      { party: 'speaker', seats:   1, votes: 34617, percentage: 0.1  },
      { party: 'ukip', seats:   1, votes: 3881099, percentage: 12.6  },
      { party: 'independent', seats:   1, votes: 17689, percentage: 0.1  },
    ],
  },
  {
    id: '2017', year: 2017, displayYear: '2017', date: '8 June 2017',
    winner: 'conservative', pm: 'Theresa May', outgoingPm: 'Theresa May',
    totalSeats: 650,
    summary: `Theresa May called a snap election expecting to increase her majority ahead of Brexit negotiations, but misread the public mood. Her campaign — centred on "strong and stable leadership" — was widely criticised as wooden. Jeremy Corbyn's Labour gained 30 seats, denying May her majority. May formed a minority government backed by the DUP through a £1 billion Confidence and Supply Agreement.`,
    highlights: [
      'May\'s gamble backfires — "strong and stable" becomes a mockery',
      'Corbyn Labour gains 30 seats, defying expectations',
      'Hung parliament: May forms minority government backed by DUP',
      '£1 billion DUP deal causes widespread controversy',
      'Two terror attacks (Manchester, London Bridge) during the campaign',
      'Youth turnout rises sharply; "youthquake" credited with Labour surge',
    ],
    youtubeId: '1PXnD5jEa-A',
    extraManifestoParties: ['cooperative', 'gpni', 'nha', 'pirate', 'ukip', 'uup', 'wep', 'welshcon', 'scottishgrn', 'welshlab', 'welshlibdem', 'scottishcon', 'scottishlab', 'scottishlibdem', 'animalpolitics', 'nicon', 'alliance', 'sdlp', 'liberal1989'],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  8, votes: 0, percentage: 33.6 },
      welshlab:    { party: 'welshlab',    seats: 28, votes: 0, percentage: 49.0 },
      welshlibdem: { party: 'welshlibdem', seats:  0, votes: 0, percentage: 4.5 },
      scottishcon: { party: 'scottishcon', seats: 13, votes: 0, percentage: 28.6 },
      scottishlab: { party: 'scottishlab', seats:  7, votes: 0, percentage: 27.1 },
      scottishlibdem: { party: 'scottishlibdem', seats:  4, votes: 0, percentage: 6.8 },
    },
    results: [
      { party: 'conservative', seats: 317, votes: 13636684, percentage: 42.3  },
      { party: 'labour', seats: 262, votes: 12877918, percentage: 40.0  },
      { party: 'snp', seats:  35, votes: 977568, percentage: 3.0  },
      { party: 'libdem', seats:  12, votes: 2371861, percentage: 7.4  },
      { party: 'dup', seats:  10, votes: 292316, percentage: 0.9  },
      { party: 'sinnfein', seats:   7, votes: 238915, percentage: 0.7  },
      { party: 'plaid', seats:   4, votes: 164466, percentage: 0.5  },
      { party: 'green', seats:   1, votes: 512327, percentage: 1.6  },
      { party: 'speaker', seats:   1, votes: 34299, percentage: 0.1  },
      { party: 'independent', seats:   1, votes: 16148, percentage: 0.1  },
    ],
  },
  {
    id: '2019', year: 2019, displayYear: '2019', date: '12 December 2019',
    winner: 'conservative', pm: 'Boris Johnson', outgoingPm: 'Boris Johnson',
    totalSeats: 650,
    summary: `Boris Johnson's Conservative Party won a majority of 80 — the largest since Thatcher's 1987 landslide — on the slogan "Get Brexit Done." The election, fought after three years of parliamentary paralysis over Britain's departure from the EU, delivered a decisive mandate. Labour, under Jeremy Corbyn, suffered its worst result since 1935. The so-called "Red Wall" — traditionally Labour working-class seats across the Midlands and the North — fell to the Conservatives for the first time in many cases.`,
    highlights: [
      '"Get Brexit Done" — Johnson wins majority of 80',
      'Red Wall collapses: Labour heartlands in the Midlands and North vote Conservative',
      'Labour\'s worst result since 1935 under Jeremy Corbyn',
      'SNP wins 48 seats, reignites Scottish independence debate',
      'Brexit completed on 31 January 2020',
      'Corbyn resigns; Keir Starmer wins Labour leadership in April 2020',
    ],
    youtubeId: '_mv7HkOx-Hs',
    manifestoPartyLabels: { reform: 'Brexit Party' },
    extraManifestoParties: ['cooperative', 'gpni', 'ukip', 'uup', 'reform', 'welshcon', 'scottishgrn', 'welshlab', 'welshlibdem', 'scottishcon', 'scottishlab', 'scottishlibdem', 'animalpolitics', 'cpa', 'gwlad', 'sdp', 'yorkshire', 'liberal1989'],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats: 14, votes: 0, percentage: 36.1 },
      welshlab:    { party: 'welshlab',    seats: 22, votes: 0, percentage: 40.9 },
      welshlibdem: { party: 'welshlibdem', seats:  0, votes: 0, percentage: 6.0 },
      scottishcon: { party: 'scottishcon', seats:  6, votes: 0, percentage: 25.1 },
      scottishlab: { party: 'scottishlab', seats:  1, votes: 0, percentage: 18.6 },
      scottishlibdem: { party: 'scottishlibdem', seats:  4, votes: 0, percentage: 9.5 },
    },
    results: [
      { party: 'conservative', seats: 365, votes: 13966454, percentage: 43.6  },
      { party: 'labour', seats: 202, votes: 10269051, percentage: 32.1  },
      { party: 'snp', seats:  48, votes: 1242380, percentage: 3.9  },
      { party: 'libdem', seats:  11, votes: 3696419, percentage: 11.5  },
      { party: 'dup', seats:   8, votes: 244128, percentage: 0.8  },
      { party: 'sinnfein', seats:   7, votes: 181853, percentage: 0.6  },
      { party: 'plaid', seats:   4, votes: 153265, percentage: 0.5  },
      { party: 'sdlp', seats:   2, votes: 118737, percentage: 0.4  },
      { party: 'green', seats:   1, votes: 835597, percentage: 2.6  },
      { party: 'speaker', seats:   1, votes: 26831, percentage: 0.1  },
      { party: 'alliance', seats:   1, votes: 134115, percentage: 0.4  },
    ],
  },
  {
    id: '2024', year: 2024, displayYear: '2024', date: '4 July 2024',
    winner: 'labour', pm: 'Keir Starmer', outgoingPm: 'Rishi Sunak',
    totalSeats: 650,
    summary: `Keir Starmer led Labour to its second-greatest landslide in history, winning 411 seats and a majority of 172 — the largest since Tony Blair's 1997 triumph. The Conservatives under Rishi Sunak were reduced to just 121 seats — their worst result since 1832. Nigel Farage's Reform UK won 5 seats but 14.3% of the national vote. The Liberal Democrats achieved 72 seats — their best result since 1923.`,
    highlights: [
      'Labour wins 411 seats — largest majority since Blair\'s 1997 landslide',
      'Conservative catastrophe: 121 seats and 23.7% — worst result since 1832',
      'Liberal Democrats win 72 seats — their best result since 1923',
      'Reform UK wins 14.3% of the vote but only 5 seats under Nigel Farage',
      'SNP collapses from 48 to just 9 seats as Labour sweeps Scotland',
      'Rishi Sunak concedes defeat in a dawn address outside Downing Street',
    ],
    youtubeId: 'l5Fr8fiNp-Y',
    extraManifestoParties: ['cooperative', 'gpni', 'workersparty', 'welshcon', 'welshlab', 'scottishcon', 'scottishlab', 'scottishlibdem', 'scottishgrn', 'alba', 'animalpolitics', 'aontu', 'cpa', 'cpb', 'nicon', 'pbp', 'rejoin', 'sdp', 'tusc', 'walesgrn', 'liberal1989'],
    partyResults: {
      welshcon:    { party: 'welshcon',    seats:  0, votes: 0, percentage: 18.2 },
      welshlab:    { party: 'welshlab',    seats: 27, votes: 0, percentage: 37.0 },
      welshlibdem: { party: 'welshlibdem', seats:  1, votes: 0, percentage: 6.5 },
      scottishcon: { party: 'scottishcon', seats:  5, votes: 0, percentage: 12.7 },
      scottishlab: { party: 'scottishlab', seats: 37, votes: 0, percentage: 35.3 },
      scottishlibdem: { party: 'scottishlibdem', seats:  6, votes: 0, percentage: 9.7 },
      scottishgrn: { party: 'scottishgrn', seats:  0, votes: 0, percentage: 3.8 },
    },
    results: [
      { party: 'labour', seats: 411, votes: 9708716, percentage: 33.7  },
      { party: 'conservative', seats: 121, votes: 6828925, percentage: 23.7  },
      { party: 'libdem', seats:  72, votes: 3519143, percentage: 12.2  },
      { party: 'snp', seats:   9, votes: 724758, percentage: 2.5  },
      { party: 'sinnfein', seats:   7, votes: 210891, percentage: 0.7  },
      { party: 'independent', seats:   6, votes: 99234, percentage: 0.3  },
      { party: 'reform', seats:   5, votes: 4117610, percentage: 14.3  },
      { party: 'dup', seats:   5, votes: 172058, percentage: 0.6  },
      { party: 'green', seats:   4, votes: 1843124, percentage: 6.4  },
      { party: 'plaid', seats:   4, votes: 194811, percentage: 0.7  },
      { party: 'sdlp', seats:   2, votes: 86861, percentage: 0.3  },
      { party: 'speaker', seats:   1, votes: 25238, percentage: 0.1  },
      { party: 'alliance', seats:   1, votes: 117191, percentage: 0.4  },
      { party: 'tuv', seats:   1, votes: 48685, percentage: 0.2  },
      { party: 'uup', seats:   1, votes: 94779, percentage: 0.3  },
    ],
  },
];

/* ── Nav structure ──────────────────────────────────────────── */
const NAV_PARTIES = {
  england: {
    label: 'England',
    parties: ['labour', 'conservative', 'libdem', 'reform', 'green', 'ukip'],
  },
  wales: {
    label: 'Wales',
    parties: ['plaid', 'reform', 'welshlab', 'welshcon', 'walesgrn', 'welshlibdem'],
  },
  scotland: {
    label: 'Scotland',
    parties: ['snp', 'scottishlab', 'reform', 'scottishgrn', 'scottishcon', 'scottishlibdem'],
  },
  'northern-ireland': {
    label: 'Northern Ireland',
    parties: ['sinnfein', 'dup', 'alliance', 'uup', 'sdlp', 'tuv', 'pbp'],
  },
  europe: {
    label: 'Europe',
    /** Principal families shown in the Parties mega-menu (matches the nation EP table). */
    megaParties: ['sand', 'epp', 'renew', 'greensefa', 'guengl', 'ecr', 'inddem'],
    parties: [
      'sand', 'epp', 'renew', 'greensefa', 'guengl', 'ecr', 'uen', 'inddem', 'identity',
      'diem25', 'volt', 'ecpm',
    ],
  },
};

const OTHERS_PARTIES = [
  'alba', 'antipartition', 'aontu', 'animalpolitics', 'binface', 'bnp', 'britainfirst', 'burningpink',
  'cooperative', 'commonwealth', 'communist', 'cpb',
  'cista', 'cpa', 'englishdemocrats', 'forwardwales', 'healthconcern',
  'independent', 'indconservative', 'indlabour', 'ilp', 'indliberal', 'indprogressive', 'indunionist',
  'irishlabour', 'irishnationalist', 'irishrepublican', 'londonreal', 'mebyon', 'nha', 'nationalindependent',
  'natlibconservative', 'nationalliberal', 'national', 'omrlp', 'onelove', 'pierscorbyn', 'pirate',
  'protestantunionist', 'reclaim',
  'referendumparty', 'rejoin', 'republicanlabour', 'respect', 'restorebrit', 'sdp', 'socialistalternative',
  'socialistlabour', 'spgb', 'liberal1989',
  'ssp', 'speaker', 'stuckist', 'tusc', 'ukup',
  'ulsterpopularunionist', 'uuuc', 'unity', 'veritas', 'wep', 'workersparty', 'yorkshire', 'yourparty',
];

const OTHERS_FEATURED = [
  'bnp', 'restorebrit', 'referendumparty', 'respect', 'tusc', 'omrlp',
];

const HOLYROOD_OTHER_PARTIES = [
  'alba', 'ssp', 'solidarity', 'rise', 'allforunity', 'isp', 'scottishfamily',
  'scottishlibertarian', 'sovereignty', 'scottishchristian', 'bnp', 'ukip',
  'cpb', 'cooperative', 'wep', 'workersparty',
];

const SENEDD_OTHER_PARTIES = [
  'ukip', 'gwlad', 'forwardwales', 'propel', 'abolish', 'heritage', 'cpb', 'tusc',
  'cooperative', 'bnp', 'respect', 'omrlp',
];

const STORMONT_OTHER_PARTIES = [
  'aontu', 'gpni', 'nicon', 'niwc', 'pbp', 'pup', 'rsf', 'sea', 'ukip', 'ukup', 'ulsterpopularunionist', 'unity', 'vanguard', 'workerspartyie'
];

const EURO_OTHER_PARTIES = [
  'changeuk', 'animalpolitics', 'englishdemocrats', 'christian', 'tuv', 'ssp', 'bnp', 'sea',
  'eurpirates',
];

const EURO_ALLIANCE_PARTIES = [
  'sand', 'epp', 'renew', 'greensefa', 'guengl', 'ecr', 'uen', 'inddem', 'identity',
  'diem25', 'volt', 'ecpm',
];

/**
 * UK parties that sat in (or were mapped to) each EP political family during
 * direct elections, 1979–2019. Used on alliance party pages for the
 * “British member parties” sidebar. Order is display order.
 */
const EURO_ALLIANCE_UK_MEMBERS = {
  sand: ['labour', 'sdlp'],
  renew: ['libdem', 'alliance'],
  epp: ['conservative', 'uup'],
  greensefa: ['green', 'snp', 'plaid', 'scottishgrn'],
  guengl: ['sinnfein'],
  ecr: ['conservative', 'uup'],
  inddem: ['ukip', 'reform'],
  identity: ['bnp'],
  uen: ['dup'],
};

/** UK MEP seats by alliance family at EP constitutive session, 1979–2019. Source: EP Review 2019 / results.elections.europa.eu */
const EURO_ALLIANCE_UK_SEATS = {
  1979: { sand: 18, epp: 61, greensefa: 1, uen: 1 },
  1984: { sand: 33, epp: 46, greensefa: 1, uen: 1 },
  1989: { sand: 46, epp: 33, greensefa: 1, uen: 1 },
  1994: { sand: 63, epp: 19, renew: 2, greensefa: 2, uen: 1 },
  1999: { sand: 30, epp: 37, renew: 10, greensefa: 6, inddem: 3, uen: 1 },
  2004: { sand: 19, epp: 28, renew: 12, greensefa: 5, guengl: 1, inddem: 12, uen: 1 },
  2009: { sand: 13, renew: 11, greensefa: 5, ecr: 25, guengl: 1, inddem: 13, identity: 2, uen: 1, other: 1 },
  2014: { sand: 20, ecr: 20, renew: 1, greensefa: 6, guengl: 1, inddem: 24, other: 1 },
  2019: { sand: 10, renew: 17, greensefa: 11, ecr: 4, guengl: 1, inddem: 29, uen: 1 },
};

function isEuroAllianceParty(partyId) {
  return EURO_ALLIANCE_PARTIES.includes(resolvePartyId(partyId));
}

function getEuroAllianceUkSeats(allianceId, year) {
  const canonical = resolvePartyId(allianceId);
  return EURO_ALLIANCE_UK_SEATS[year]?.[canonical] ?? 0;
}

function getEuroAllianceUkMembers(allianceId) {
  const canonical = resolvePartyId(allianceId);
  const ids = EURO_ALLIANCE_UK_MEMBERS[canonical] || [];
  return ids.filter(pid => PARTIES[pid]);
}

const DEVOLVED_PORTALS = {
  holyrood: {
    id: 'holyrood',
    label: 'Scottish Parliament',
    subtitle: 'Holyrood',
    nation: 'scotland',
    body: 'Scottish Parliament',
    established: 1999,
    members: 129,
    system: 'Additional Member System',
    description: 'The Scottish Parliament at Holyrood was established in 1999. It elects 129 MSPs and has primary legislative responsibility for devolved matters including health, education, justice, and transport in Scotland.',
  },
  senedd: {
    id: 'senedd',
    label: 'Welsh Parliament',
    subtitle: 'Senedd Cymru',
    nation: 'wales',
    body: 'Senedd Cymru',
    established: 1999,
    members: 96,
    system: 'Closed list PR (from 2026); AMS (1999–2021)',
    description: 'The Senedd Cymru — Welsh Parliament — was established in 1999 after a referendum passed by just 6,721 votes. From 2026 it has 96 Members elected by closed-list proportional representation; previously 60 Members were elected under the Additional Member System.',
  },
  stormont: {
    id: 'stormont',
    label: 'Northern Ireland Assembly',
    subtitle: 'Stormont',
    nation: 'northern-ireland',
    body: 'Northern Ireland Assembly',
    established: 1998,
    members: 90,
    system: 'Single Transferable Vote',
    description: 'The Northern Ireland Assembly at Stormont was established under the Good Friday Agreement. Its 90 MLAs are elected by STV and the Executive requires cross-community support.',
  },
  london: {
    id: 'london',
    label: 'London Mayor & Assembly',
    subtitle: 'City Hall',
    nation: 'england',
    body: 'Greater London Authority',
    established: 2000,
    members: 25,
    system: 'Supplementary Vote / AMS',
    description: 'The Greater London Authority comprises an elected Mayor and 25 Assembly Members. The Mayor holds executive powers over transport, policing, housing, and economic development in the capital.',
  },
  euro: {
    id: 'euro',
    label: 'European Parliament',
    subtitle: 'Strasbourg & Brussels',
    nation: 'uk',
    body: 'European Parliament (UK MEPs)',
    established: 1979,
    members: 73,
    system: 'Proportional Representation (1999–2019); FPTP (1979–1994)',
    description: 'The UK participated in European Parliament elections from the first direct elections in 1979 until its departure from the EU in 2020. UK MEPs were elected under First Past the Post (1979–1994) and regional list Proportional Representation (1999–2019).',
  },
};

/** Manifesto/party slug → canonical party page. */
const PARTY_ALIASES = {
  pes: 'sand',
  eldr: 'renew',
  alde: 'renew',
  greengroup: 'greensefa',
  eurengreens: 'greensefa',
  eurefa: 'greensefa',
  eurleft: 'guengl',
  ecrp: 'ecr',
  eaf: 'identity',
  awp: 'animalpolitics', // London folder slug for Animal Welfare Party
  brexit: 'reform', // Brexit Party relaunched as Reform UK (2021); EP folder slug retained
};

function resolvePartyId(id) {
  return PARTY_ALIASES[id] || id;
}

function euroManifestoSlugsForParty(partyId) {
  const canonical = resolvePartyId(partyId);
  const slugs = new Set([partyId, canonical]);
  Object.entries(PARTY_ALIASES).forEach(([alias, target]) => {
    if (target === canonical) slugs.add(alias);
  });
  return [...slugs];
}

/* ── Helpers ────────────────────────────────────────────────── */
function getNationLabel(id) {
  return NATIONS[id]?.name || NAV_PARTIES[id]?.label || id;
}
function getPartyColor(id, year) {
  const pid = resolvePartyId(id);
  if ((pid === 'libdem' || pid === 'liberal') && year && year < 1988) {
    return '#FFD700'; // Pre-1989 Liberal Party yellow
  }
  return PARTIES[pid]?.color || '#6b7280';
}
function getPartyDim(id)   { return PARTIES[resolvePartyId(id)]?.dim   || 'rgba(107,114,128,0.14)'; }

function nationPartyLinkHtml(pid) {
  const p = PARTIES[pid];
  if (!p) return '';
  const raw = p.color;
  const kicker = typeof partyTextColour === 'function' ? partyTextColour(pid) : raw;
  const dot = typeof dotStyle === 'function' ? dotStyle(raw) : `background:${raw}`;
  return `<a href="/party/${pid}" class="nation-party-link" style="--party-color:${kicker}">
    <span class="nation-party-dot" style="${dot}"></span>
    <span>${p.shortName}</span>
  </a>`;
}

/** Liberal / SDP Alliance / Liberal Democrats — period-correct labels when year is given. */
const LIBERAL_LINEAGE_NAMES = {
  libdem:         { liberal: 'Liberal', alliance: 'Alliance', modern: 'Liberal Democrats' },
  welshlibdem:    { liberal: 'Liberal', alliance: 'Alliance', modern: 'Welsh Liberal Democrats' },
  scottishlibdem: { liberal: 'Liberal', alliance: 'Alliance', modern: 'Scottish Liberal Democrats' },
};

/** Green Party of England and Wales — Ecology Party before the 1985 rename. */
const GREEN_LINEAGE_NAMES = {
  green: { ecology: 'Ecology Party', modern: 'Green Party' },
};

/** Reform UK — Brexit Party before the 2021 relaunch. */
const REFORM_LINEAGE_NAMES = {
  reform: { brexit: 'Brexit Party', modern: 'Reform UK' },
};

function getPartyName(id, year) {
  const pid = resolvePartyId(id);
  const p = PARTIES[pid];
  if (!p) return id;
  if (year != null && LIBERAL_LINEAGE_NAMES[pid]) {
    const names = LIBERAL_LINEAGE_NAMES[pid];
    if (year < 1983) return names.liberal;
    if (year === 1983 || year === 1987) return names.alliance;
    return names.modern;
  }
  if (year != null && GREEN_LINEAGE_NAMES[pid]) {
    const names = GREEN_LINEAGE_NAMES[pid];
    if (year < 1985) return names.ecology;
    return names.modern;
  }
  if (year != null && REFORM_LINEAGE_NAMES[pid]) {
    const names = REFORM_LINEAGE_NAMES[pid];
    if (year < 2021) return names.brexit;
    return names.modern;
  }
  return p.shortName;
}
function getElection(id)   { return ELECTIONS.find(e => e.id === id); }
function getMajorityThreshold(n) { return Math.floor(n / 2) + 1; }

function devolvedPartyLink(id, label, year) {
  const canonical = resolvePartyId(id);
  const name = label || getPartyName(canonical, year);
  if (!canonical || canonical === 'others' || !PARTIES[canonical]) return name;
  return `<a href="/party/${canonical}" class="inline-party-link">${name}</a>`;
}

function normalizeDevolvedElection(electionOrYear) {
  if (electionOrYear && typeof electionOrYear === 'object') return electionOrYear;
  const year = electionOrYear;
  return { year, displayYear: String(year) };
}

/** Trim copy for meta description tags (~155 characters). */
function truncateMetaDescription(text, maxLen = 155) {
  if (!text) return '';
  if (text.length <= maxLen) return text;
  const cut = text.slice(0, maxLen);
  const sp = cut.lastIndexOf(' ');
  return `${(sp > 80 ? cut.slice(0, sp) : cut).trimEnd()}…`;
}

/** First sentence or short excerpt — used as the visible party lede. */
function partyLedeText(description) {
  if (!description) return '';
  const m = description.match(/^[^.!?]+[.!?]/);
  if (m && m[0].length <= 180) return m[0].trim();
  return truncateMetaDescription(description, 155);
}

/** Build chamber labels such as "14 Westminster · 7 Senedd". */
function formatPartyChamberParts(counts, isAlliance = false) {
  if (!counts) return [];
  const parts = [];
  if (!isAlliance && counts.westminster) parts.push(`${counts.westminster} Westminster`);
  if (!isAlliance && counts.holyrood) parts.push(`${counts.holyrood} Holyrood`);
  if (!isAlliance && counts.senedd) parts.push(`${counts.senedd} Senedd`);
  if (!isAlliance && counts.stormont) parts.push(`${counts.stormont} Stormont`);
  if (counts.euro) parts.push(`${counts.euro} European Parliament`);
  return parts;
}

/** Meta description for party pages — lede plus chamber scope when available. */
function buildPartyMetaDescription(party, chamberParts) {
  const lede = partyLedeText(party.description);
  if (!chamberParts || !chamberParts.length) {
    return truncateMetaDescription(
      party.description || `Manifestos and election history for ${party.shortName || party.name}.`,
      155,
    );
  }
  return truncateMetaDescription(
    `${lede} Browse manifestos and results across ${chamberParts.join(', ')}.`,
    155,
  );
}

/** Browse-by-party card (homepage and other-parties listings). */
function buildPartyBrowseCard(pid, opts = {}) {
  const p = PARTIES[pid];
  if (!p) return '';
  const name = opts.fullName ? p.name : (p.shortName || p.name);
  const accent = typeof partyAccentDerived === 'function'
    ? partyAccentDerived(pid)
    : { surface: p.color, kicker: p.color };
  const foundedKicker = p.founded ? `EST. ${p.founded}` : '';
  const subline = opts.meta
    ? `${p.spectrum}${p.founded ? ` · Est. ${p.founded}` : ''}`
    : foundedKicker;
  const holdingsLine = typeof formatPartyHoldingsLine === 'function'
    ? formatPartyHoldingsLine(pid)
    : '';
  const headerHtml = opts.meta
    ? `<div class="party-card-name">${name}</div><div class="party-card-founded">${subline}</div>`
    : `<div><span class="party-card-name">${name}</span>${foundedKicker ? `<span class="party-card-founded">${foundedKicker}</span>` : ''}</div>`;
  return `<a href="/party/${pid}" class="party-card" style="--party-surface:${accent.surface};--party-kicker:${accent.kicker}">
    <div class="party-card-edge"></div>
    <div class="party-card-body">
      ${headerHtml}
      <div class="party-card-desc">${p.description}</div>
      ${holdingsLine ? `<div class="party-card-holdings">${holdingsLine}</div>` : ''}
    </div>
  </a>`;
}

/** Controlling / largest party id for a devolved portal index entry. */
function devolvedElectionWinnerPartyId(e) {
  if (e.mayorWinner) return resolvePartyId(e.mayorWinner);
  const results = e.results || [];
  const control = e.control ? resolvePartyId(e.control) : null;
  // Prefer control when it (or an alias) appears in seat results.
  if (control && results.some(r => resolvePartyId(r.party) === control)) return control;
  const top = results.slice().sort((a, b) => (b.seats || 0) - (a.seats || 0))[0];
  return (top?.party ? resolvePartyId(top.party) : null) || control || null;
}

function devolvedTimelinePartyColor(e) {
  const pid = devolvedElectionWinnerPartyId(e);
  if (!pid || !PARTIES?.[pid]) return 'var(--gold)';
  return getPartyColor(pid, e.year);
}

/** Winner kicker text for devolved portal election cards (mirrors Westminster cards). */
function devolvedElectionWinnerLabel(e) {
  const pid = devolvedElectionWinnerPartyId(e);
  const result = (e.results || []).find(r => r.party === pid);
  const seats = result?.seats || 0;
  const party = pid && PARTIES?.[pid];
  const name = result?.partyLabel
    || (party ? (party.shortName || party.name) : '')
    || e.winnerName
    || '';
  const body = e.body;

  if (body === 'euro') {
    return seats ? `${name} · ${seats} MEPs` : name;
  }
  if (body === 'gla' || e.mayorWinner) {
    return seats ? `${name} · ${seats} Assembly seats` : name;
  }

  const threshold = e.majorityThreshold
    || (e.totalSeats ? Math.floor(e.totalSeats / 2) + 1 : 0);
  if (seats && threshold && seats < threshold) {
    return `${name} minority · ${seats} seats`;
  }
  return seats ? `${name} · ${seats} seats` : name;
}

/** Person line under the winner kicker (First Minister / Mayor / FM & dFM). Omit for Europe. */
function devolvedElectionPersonLine(e) {
  if (e.body === 'euro') return '';
  if (e.firstMinister && e.deputyFirstMinister) {
    return `FM &amp; dFM: <span>${e.firstMinister} &amp; ${e.deputyFirstMinister}</span>`;
  }
  if (e.firstMinister) {
    return `First Minister: <span>${e.firstMinister}</span>`;
  }
  if (e.mayorWinner && e.winnerName) {
    return `Mayor: <span>${e.winnerName}</span>`;
  }
  return '';
}

/** Shared portal election card — same structure as Westminster `electionCardHtml`. */
function buildDevolvedTimelineCard(href, e) {
  const theme = typeof getCurrentTheme === 'function' ? getCurrentTheme() : 'dark';
  const pid = devolvedElectionWinnerPartyId(e);
  const accent = (typeof partyAccentDerivedForYear === 'function' && pid)
    ? partyAccentDerivedForYear(pid, e.year, theme)
    : {
        surface: devolvedTimelinePartyColor(e),
        kicker: devolvedTimelinePartyColor(e),
        border: 'rgba(255,255,255,0.07)',
        raw: devolvedTimelinePartyColor(e),
      };
  const ghostDigits = String(e.displayYear || e.year).replace(/\D/g, '').slice(-2)
    || String(e.year).slice(-2);
  const longLabel = String(e.displayYear || '').includes(' ')
    || String(e.displayYear || '').length > 5;
  const ghostColour = typeof ghostTint === 'function'
    ? ghostTint(accent.raw, theme)
    : (typeof rgbaHex === 'function' ? rgbaHex(accent.raw, 0.07) : accent.raw);
  const personLine = devolvedElectionPersonLine(e);
  const personHtml = personLine ? `<div class="card-pm">${personLine}</div>` : '';
  const seatBar = typeof electionSeatBarHtml === 'function' ? electionSeatBarHtml(e) : '';

  return `<a href="${href}" class="election-card" data-winner="${pid || ''}" style="--party-border:${accent.border};--party-ghost:${ghostColour};--party-kicker:${accent.kicker};--party-surface:${accent.surface}">
    <div class="card-ghost-year" aria-hidden="true">${ghostDigits}</div>
    <div class="card-year${longLabel ? ' long-label' : ''}">${e.displayYear}</div>
    <div class="card-date">${e.date || ''}</div>
    <div class="card-winner"><div class="card-winner-dot"></div>${devolvedElectionWinnerLabel(e)}</div>
    ${personHtml}
    <div class="card-seats-bar">${seatBar}</div>
  </a>`;
}

/**
 * Shared PDF call-to-action markup (I06).
 * @param {{ href: string, size?: string, compact?: boolean, scanNote?: boolean }} opts
 */
function pdfCtaHtml({ href, size = '', compact = false, scanNote = true } = {}) {
  if (!href) return '';
  const sizePart = size ? ` · ${size}` : '';
  if (compact) {
    return `<a href="${href}" class="manifesto-link" target="_blank" rel="noopener">
          <span class="manifesto-link-icon" aria-hidden="true">📄</span>
          <div class="manifesto-link-info"><div class="manifesto-link-title">Original PDF${sizePart}</div></div>
        </a>`;
  }
  const sub = scanNote
    ? `PDF scan of original document${sizePart}`
    : (size ? `PDF document${sizePart}` : 'PDF document');
  return `<a href="${href}" class="manifesto-link" target="_blank" rel="noopener">
          <span class="manifesto-link-icon" aria-hidden="true">📄</span>
          <div class="manifesto-link-info"><div class="manifesto-link-title">Original PDF</div><div class="manifesto-link-sub">${sub}</div></div>
        </a>`;
}

/** Shared manifesto card for Holyrood, Senedd, Stormont, and European elections. */
function buildDevolvedManifestoCard(m, electionOrYear, opts = {}) {
  const election = normalizeDevolvedElection(electionOrYear);
  const pid = m.party;
  const yearNum = election.year;
  const yearLabel = election.displayYear || String(yearNum || '');
  const pageId = opts.partyPageId || resolvePartyId(pid);
  const color = opts.color || getPartyColor(pageId, yearNum);
  const dim = opts.dim || getPartyDim(pageId) || 'rgba(0,0,0,0.04)';
  const partyName = opts.partyName
    || m.partyLabel
    || (typeof getEuroAllianceManifestoLabel === 'function'
      ? getEuroAllianceManifestoLabel(pid, yearNum)
      : null)
    || getPartyName(pageId, yearNum);
  const pdfSize = (typeof window.getPdfSize === 'function' && m.pdf) ? window.getPdfSize(m.pdf) : '';
  const headerName = pageId && PARTIES[pageId]
    ? devolvedPartyLink(pageId, partyName, yearNum)
    : partyName;
  const altHeading = m.candidate || partyName;
  const assetsVersion = typeof ASSETS_VERSION !== 'undefined' ? ASSETS_VERSION : '';
  const pdfLink = m.pdf
    ? pdfCtaHtml({ href: m.pdf, size: pdfSize, scanNote: true })
    : '';

  return `
    <div class="manifesto-card" style="--party-color:${color};--party-dim:${dim}">
      <a href="${m.pdf}" class="manifesto-thumb" target="_blank" rel="noopener" aria-label="Open the ${altHeading} manifesto PDF">
        <img src="${m.cover}?v=${assetsVersion}" alt="${altHeading} manifesto cover"
          class="img-lazy" loading="lazy" decoding="async"
          onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
        <div class="manifesto-thumb-placeholder" style="display:none">
          <svg viewBox="0 0 48 64" fill="none" xmlns="http://www.w3.org/2000/svg" class="thumb-doc-icon">
            <rect x="12" y="10" width="32" height="44" rx="2" fill="currentColor" opacity="0.9"/>
          </svg>
          <span class="thumb-year">${yearLabel}</span>
        </div>
      </a>
      <div class="manifesto-card-header">
        <div class="manifesto-party-dot" style="background:${color}"></div>
        <div class="manifesto-party-name">${headerName}</div>
        <div class="manifesto-party-tag">${yearLabel}</div>
      </div>
      <div class="manifesto-card-body">
        ${m.candidate ? `<p class="london-manifesto-title">${m.candidate}</p>` : ''}
        ${m.title && !m.candidate ? `<p class="london-manifesto-title">${m.title}</p>` : ''}
        ${pdfLink}
      </div>
    </div>`;
}
