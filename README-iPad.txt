WEBサカ選手検索 v4 — iPad/iPhone 更新手順

v3のデータ・お気に入り・比較機能を残し、適性エリア検索、11人チーム保存、能力値・適性の比較を追加します。

重要：既存の players.json は削除しないでください。GitHub Actionsが新しいデータを生成します。

1. ZIPをiPadの「ファイル」アプリで解凍。
2. GitHub https://github.com/v529h2gs25-cell/websaka-search をSafariで開く。
3. index.html をv4の index.html に置き換えて Commit changes。
4. collect.py をv4の collect.py に置き換えて Commit changes。
5. .github/workflows/update-players.yml をv4の同名ファイルに置き換えて Commit changes。
   ※iPadで既存ファイルを上書きアップロードできない場合はGitHubの鉛筆アイコンで内容を置き換える。
6. Actions → Update WEBsaka players → Run workflow を実行。
7. Collect players と Check player count before publishing が緑のチェックか確認。
8. 公開サイト https://v529h2gs25-cell.github.io/websaka-search/ を再読み込み。

注意：元サイトのHTMLにより、適性・能力値の抽出が失敗する可能性があります。
抽出率が80%未満の場合は意図的に更新を失敗させ、既存のplayers.jsonを保持します。
その場合はGitHub Actionsの「Extended aptitude/ability fields parsed」のログを確認してください。
既存のv3データでは適性・能力値は未取得扱いとなります。

適性表：元サイトの表示順で上から5段、各段の左・中央・右（GKは中央のみ）として記録。
能力値：元サイトに掲載された3数値を掲載順に表示。名称は元サイトの意味が確定するまで付けていません。
チームはブラウザのローカル保存です。別端末へは同期されません。
自動更新：毎週月曜日12:17頃（日本時間）。GitHubのスケジュール実行には遅延があり得ます。
