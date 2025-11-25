# Common

Common module for the project.

## Packet

定義所以傳送的封包格式，由 `class Packet` 定義。

### Attributes

1. type: string
   定義封包的類別，例如 `LOGIN`、`LOGOUT`、`MESSAGE` 等等
2. data: dict
   定義封包的內容，例如
   ```json
   {
     "username": "user1",
     "password": "password1"
   }
   ```

### Types

#### Auth Types

1. T_LOGIN
2. T_REGISTER
3. T_LOGOUT

#### Auth Packets

1. LoginPacket

   ```json
   {
     "type": "LOGIN",
     "data": {
       "username": "user1",
       "password": "password1"
     }
   }
   ```

2. RegisterPacket

   ```json
   {
     "type": "REGISTER",
     "data": {
       "username": "user1",
       "password": "password1"
     }
   }
   ```

3. LogoutPacket
   ```json
   {
     "type": "LOGOUT",
     "data": {}
   }
   ```

#### Database Packets

Database 回覆 lobby server 的封包

1. DBLoginPacket

   ```json
   {
     "type": "LOGIN",
     "data": {
       "success": true
     }
   }
   ```

2. DBRegisterPacket

   ```json
   {
     "type": "REGISTER",
     "data": {
       "success": true
     }
   }
   ```

3. DBLogoutPacket
   ```json
   {
     "type": "LOGOUT",
     "data": {
       "success": true
     }
   }
   ```
