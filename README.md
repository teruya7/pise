# pise
Pydefect Integrated Support Environment  (pise) is a collection of tools that supports pydefect users to prepare input files for the VASP calculations, submit calculations, analyze its results and summarize them in .md files automatically.

#環境構築
1. 必要なライブラリ
- vise
- pydefect
- python-fire

2. piseのダウンロード  
   ```git clone -b master https://github.com/teruya7/pise/```
3. 各種設定
- ```alias pise="python /home/usr1/r70391a/pise/pise_main.py"```を.zshrcに追記
- .pise_defaults.yamlのnullの部分に適切な内容を記入する。  
  ```cp pise/.pise_defaults.yaml ~/```
     
  ```
    #Materials projectのAPI key
    MY_API_KEY: null #必須
    
    #スパコンの環境変数の設定
    limit_jobs: null #スパコンのジョブ数の上限
    num_jobs_command: null　#スパコンのジョブ数を出力するコマンド
    submit_command: null #スパコンのジョブを投げるコマンド　#必須
    submission_ready: ready_for_submission.txt
    job_script_path: null　#ジョブスクリプトがあるパスを書く　#必須
    
    #job_scriptの設定
    job_script_small: run6.4.1_1.sh　#軽い計算に用いるジョブスクリプトの名前　#必須
    small_task: ["opt", "band", "dos"]
    job_script_large: run6.4.1_4.sh　#重い計算に用いるジョブスクリプトの名前　#必須
    large_task: ["defect", "dielectric", "dielectric_rpa", "band_nsc",  "abs"]```

#具体例（Li2S_mp-1153）
1. target_info.jsonの作成（計算対象を管理するファイル）  
   ```pise tar add mp-1153```でmaterials projectから計算対象のデータを取得する。
         
   target_info.json  
   ```
   [{
        "material_id": "mp-1153",
        "formula_pretty": "Li2S",
        "elements": ["Li", "S"]
    }]
   ```

2. 構造最適化の計算インプットを作成  
   ```pise pre```でtarget_info.jsonを読み込み、計算対象のディレクトリを作成し、構造最適化計算のインプットを作成する。

3. 計算を投げる  
   ```pise submit all```でready_for_submission.txtが存在するフォルダの計算を投げる。
   引数allをunitcell, cpd, defectに変更することで計算を投げるディレクトリの種類を指定できる。

4. 欠陥計算の作業フローを進める   
   ```pise pre```は計算の進捗をcalc_info.jsonから判断し、欠陥計算の作業フロー通りに計算インプットを作成することができる。計算インプットを作成したら、```pise submit all```で計算を投げる。上記の2つのコマンドだけで欠陥計算の作業フローを進めることができる。  

5. 計算結果の解析を行う    
   ```pise ana```で計算の進捗をcalc_info.jsonから判断し、欠陥計算の解析を行う。  

6. 解析結果を集める  
   ```pise sum```で計算結果をsummary_info.jsonにまとめる。
   
7. 解析結果を.md形式でまとめる
   ```pise md```で計算結果を.md形式でまとめる。  