$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$session.UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36"
$session.Cookies.Add((New-Object System.Net.Cookie("_fuid", "YWI1NjEyMmMtMjlmMC00ZWM1LWI3ZTctNzQzZjY2ZGU5NDNk", "/", ".qualer.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("__utmz", "147229740.1757527976.45.2.utmcsr=excel.officeapps.live.com|utmccn=(referral)|utmcmd=referral|utmcct=/", "/", ".jgiquality.qualer.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("GUID", "`"acadcd3b-26e1-441a-a0fe-db75e2088e55`"", "/", ".qualer.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("__RequestVerificationToken_L3NoYXJlZC1zZWN1cmVk0", "IUVgIlmwo3zgnUwGBQxc7XN2T3fA1aXYJ7AhxdjyeDwd2ndcZCPjmgMVN-cd9Zqs0z8Y1JzfJ1-lCzGuqxygqF5HztQ1", "/", "jgiquality.qualer.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("__utmc", "147229740", "/", ".jgiquality.qualer.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("__utma", "147229740.1751280352.1751238350.1767652796.1767734700.120", "/", ".jgiquality.qualer.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("Qualer.Employee.Login.SessionId", "dc4ae825845849e48fd6587fa41d0f50", "/", "jgiquality.qualer.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("Qualer.auth", "1BDCDA37D1F8A34957C8E858A3F8ADC299EC87595650C87E024FE080CE22B63B094E8FAC50B1669BF48F7B9F3FB96E9C39A963C697927D7C47F644AC8A2B4EB9EEBE6347183A54982BD8872BDCF07829F580E07A1E1CCFC506CFFCD7D4250FC7ABE3424148DFC6DAF8F2AA4604E08F0696836C6F020A6DFD00F0B005A31EECD2A8593A88F4936AEAE6541C33353C4A6BC01F5125", "/", "jgiquality.qualer.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("__utmt_UA-62779523-2", "1", "/", ".jgiquality.qualer.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("__utmb", "147229740.27.10.1767734700", "/", ".jgiquality.qualer.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("ASP.NET_SessionId", "tde3h5ulcsfz2anhxrq0nv32", "/", "jgiquality.qualer.com")))
$session.Cookies.Add((New-Object System.Net.Cookie("RT", "`"z=1&dm=qualer.com&si=a97cc615-8778-4ba6-a180-0759bf590f61&ss=mk33lix9&sl=87&tt=3zli&bcn=https%3A%2F%2Fmetrics.qualer.com%2Fapi%2Fmetrics&ld=224ns`"", "/", ".qualer.com")))
Invoke-WebRequest -UseBasicParsing -Uri "https://jgiquality.qualer.com/ClientDashboard/Clients_Read" `
-Method "POST" `
-WebSession $session `
-Headers @{
"authority"="jgiquality.qualer.com"
  "method"="POST"
  "path"="/ClientDashboard/Clients_Read"
  "scheme"="https"
  "accept"="*/*"
  "accept-encoding"="gzip, deflate, br, zstd"
  "accept-language"="en-US,en;q=0.9"
  "cache-control"="no-cache, must-revalidate"
  "clientrequesttime"="2026-01-06T16:23:10"
  "origin"="https://jgiquality.qualer.com"
  "pragma"="no-cache"
  "priority"="u=1, i"
  "referer"="https://jgiquality.qualer.com/clients"
  "sec-ch-ua"="`"Google Chrome`";v=`"143`", `"Chromium`";v=`"143`", `"Not A(Brand`";v=`"24`""
  "sec-ch-ua-mobile"="?0"
  "sec-ch-ua-platform"="`"Windows`""
  "sec-fetch-dest"="empty"
  "sec-fetch-mode"="cors"
  "sec-fetch-site"="same-origin"
  "x-requested-with"="XMLHttpRequest"
} `
-ContentType "application/x-www-form-urlencoded; charset=UTF-8" `
-Body "sort=ClientCompanyName-asc&page=1&pageSize=1000000&group=&filter=&search=&filterType=AllClients&__RequestVerificationToken=tUVqA_gNGpID33vH4BpXjO3UB4_RwVPX0TJYes3IDDTriiWpV4KsmNmvQIHwryTcdtTqzyMNBhnJNeLGUf2GFTi7b1iLXRZGfd6eqjcwEXcAr1Zx0" `
-OutFile "clients.json"