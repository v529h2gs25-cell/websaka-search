WEBサカ 選手検索

1. index.html を開くと13ページ目の確認済みデータで検索できます。
2. 全56ページを取り込むには、サイトの利用条件・robots.txtを確認のうえ、
   pip install requests beautifulsoup4
   python collect.py
   を実行します（インターネット接続が必要）。
3. python -m http.server 8000 を実行して http://localhost:8000 を開くと
   players.json が自動読み込みされます。
4. 公開する場合は index.html と players.json を同じディレクトリに置いて
   GitHub Pages / Netlify 等へ配置します。

注意：収集スクリプトは元サイトのHTML変更により修正が必要になる場合があります。
本環境では全56ページの収集実行を検証できていません。
