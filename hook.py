from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

datas = collect_data_files('go_engine')
binaries = collect_dynamic_libs('go_engine')
hiddenimports = ['go_engine']