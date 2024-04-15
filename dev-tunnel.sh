zsh
source ~/.zshrc
devtunnel login
devtunnel create --allow-anonymous
devtunnel port create -p 8080
devtunnel host