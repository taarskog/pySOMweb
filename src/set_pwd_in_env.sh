# Reduce exposure of pwd by setting it in an environment variable
read -s -p "SOMweb pwd: " SOMwebPwd
echo
export SOMwebPwd
echo "You can now reference \$SOMwebPwd as pwd in calls to main.py if this script was called as 'source ./set_pwd_in_env.sh'"
