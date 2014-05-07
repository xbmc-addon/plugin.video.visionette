cd `dirname $0`/../src

OLD=`cat ./addon.xml | grep '<addon' | grep 'version="' | grep -E -o 'version="[0-9\.]+"' |  grep -E -o '[0-9\.]+'`
echo "Old version: $OLD"
echo -n 'New version: '
read NEW

sed -e "s/Visionette\" version=\"$OLD\"/Visionette\" version=\"$NEW\"/g" ./addon.xml > ./addon2.xml
mv ./addon2.xml ./addon.xml

rm -rf ../plugin.video.visionette
rm -f ./plugin.video.visionette.zip
mkdir ../plugin.video.visionette
cp -r ./* ../plugin.video.visionette/

cd ../
zip -rq ./plugin.video.visionette.zip ./plugin.video.visionette

cp ./plugin.video.visionette.zip ../repository.hal9000/repo/plugin.video.visionette/plugin.video.visionette-$NEW.zip

rm -rf ./plugin.video.visionette
rm -f ./plugin.video.visionette.zip

`../repository.hal9000/build/build.sh`
