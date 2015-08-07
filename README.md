Run:
./serv.py

Create:
curl --header 'X-AUTH-TOKEN: 123' 127.0.0.1:8888/1/servers/create --data "name=new serv"

View servers list:
curl --header 'X-AUTH-TOKEN: 123' 127.0.0.1:8888/1/servers/

View server status:
curl --header 'X-AUTH-TOKEN: 123' 127.0.0.1:8888/1/servers/1

Delete server:
curl --header 'X-AUTH-TOKEN: 123' -X DELETE 127.0.0.1:8888/1/servers/3

Tests:
test/test.py

*warning: tests run for about 30 seconds
