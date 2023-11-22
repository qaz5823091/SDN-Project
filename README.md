# SDN Project
## 環境
預設系統 Ubuntu

## Mininet
* 安裝 mininet install mininet
```bash
$ sudo apt-get install mininet
```

* 建立拓樸並開啟 controller 與 nat 模式 launch mininet with defined topology
```bash
$ sudo mn --topo single,5 --mac --switch ovsk --controller remote --nat
```

* 看到以下畫面即表示成功 success if you see the picture below
![image](https://hackmd.io/_uploads/Sy3yixYEa.png)


## 環境建立（需新開終端機）
* 建立 `venv` 虛擬環境 create a virtual environment named `venv`
```bash
$ virtualenv venv
```

* 啟動虛擬環境 launch the virtual environment
```bash
$ source venv/bin/activate
```

* 下載獎勵式學習系統 clone repo from Github
```bash
$ git clone https://github.com/qaz5823091/SDN-Project.git
```

* 重新命名目錄 rename the directory
```bash
$ mv SDN-Project/ project/
```

* 安裝套件 install target packages
```bash
(venv) $ pip install -r project/requirements.txt
```

## Controller
* 下載 ryu clone ryu controller from Github
```bash
$ git clone https://github.com/faucetsdn/ryu.git
```

* 把系統放在 ryu/app 底下 move the project directory to the ryu/app/
```bash
$ mv project/ ryu/ryu/app/project/
```

* 進入 ryu/ 目錄 enter the ryu directory
```bash
$ cd ryu
```

* 啟動虛擬環境 launch the virtual environment
```bash
$ source venv/bin/activate
```

* 啟動 controller 程式 start ryu application
```bash
(venv) $ sh ryu/app/project/auto-start.sh
```

* 看到以下畫面即表示成功 success if you see the picture below
![image](https://hackmd.io/_uploads/HJVrogtNT.png)

* 伺服器會架設在 port 8080 API server is setup on localhost:8080


## Web（需新開終端機）
* 啟動虛擬環境 launch the virtual environment
```bash
$ source venv/bin/activate
```

* 進入網頁的目錄 enter ryu/ryu/app/project/web/
```bash
(venv) $ cd ryu/ryu/app/project/web/
```

* 啟動網頁 launch the flask server
```bash
(venv) $ flask run
```

* 系統會假設在 port 5000 rewarded learning system is setup on localhost:5000
![image](https://hackmd.io/_uploads/rkCWy-KVp.png)

## 注意！Notice!
瀏覽器需安裝允許 CORS 的插件，網頁才會運作正常
- [Chrome](https://chromewebstore.google.com/detail/allow-cors-access-control/lhobafahddgcelffkeicbaginigeejlf?pli=1)
- [Firefox](https://addons.mozilla.org/zh-TW/firefox/addon/access-control-allow-origin/)
