sed -i 's+wss://+ws://+g' multiplayer/templates/javascript/durak.js
sed -i 's+wss://+ws://+g' account/templates/javascript/base.js
git pull origin
sed -i 's+ws://+wss://+g' multiplayer/templates/javascript/durak.js
sed -i 's+ws://+wss://+g' account/templates/javascript/base.js