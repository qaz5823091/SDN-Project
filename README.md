# SDN Project
## 環境
- Docker
- Dcoker Compose

## 安裝
1. 按照[官網](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository)提示安裝  `docker`、`docker-compose`

2. 新增 domain 到 host
```bash
$ sudo echo $'172.20.0.2 console.sdn.com\n172.20.0.3 api.sdn.com' >> /etc/hosts
```
> 需要輸入此行 API 呼叫才會正常

3. 複製專案
```bash
$ git clone git@github.com:qaz5823091/SDN-Project.git
$ cd SDN-Project/
```

4. 開啟 console 與 api 網站
```bash
(SDN-Project) $ docker compose up console api
```
> 可加入 `-d` 參數在背後執行（但這樣無法觀測到數據）

5. 開啟 mininet 網路（開啟另一個終端機）
```bash
(SDN-Project) $ docker compouse run --rm mininet
```
<details>
<summary>其他設定</summary>
5-1. 若需要開啟其他拓樸可以到 `docker-compose.yml` 修改

```yml=42
command: "--topo single,5 --mac --switch ovsk --controller remote,ip=172.20.0.3 --nat"
```

5-2. 或是將其註解，開啟容器並手動輸入 mn 指令
</details>

6. 瀏覽器輸入 `console.sdn.com` 可進到控制台畫面

7. 再來就可以開始實驗了！

## 注意！Notice!
瀏覽器需安裝允許 CORS 的插件，網頁才會運作正常
- [Chrome](https://chromewebstore.google.com/detail/allow-cors-access-control/lhobafahddgcelffkeicbaginigeejlf?pli=1)
- [Firefox](https://addons.mozilla.org/zh-TW/firefox/addon/access-control-allow-origin/)