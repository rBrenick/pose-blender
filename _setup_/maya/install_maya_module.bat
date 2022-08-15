
:: pose_blender is determined by the current folder name
for %%I in (.) do set pose_blender=%%~nxI
SET CLEAN_pose_blender=%pose_blender:-=_%

:: Check if modules folder exists
if not exist %UserProfile%\Documents\maya\modules mkdir %UserProfile%\Documents\maya\modules

:: Delete .mod file if it already exists
if exist %UserProfile%\Documents\maya\modules\%pose_blender%.mod del %UserProfile%\Documents\maya\modules\%pose_blender%.mod

:: Create file with contents in users maya/modules folder
(echo|set /p=+ %pose_blender% 1.0 %CD%\_setup_\maya & echo; & echo icons: ..\%CLEAN_pose_blender%\icons)>%UserProfile%\Documents\maya\modules\%pose_blender%.mod

:: end print
echo .mod file created at %UserProfile%\Documents\maya\modules\%pose_blender%.mod



