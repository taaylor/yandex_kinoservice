#!/bin/sh

until mongosh --host mongodb_cfg1 --eval "rs.initiate({_id: \"mongors1conf\", configsvr: true, members: [{_id: 0, host: \"mongodb_cfg1:27017\"}, {_id: 1, host: \"mongodb_cfg2:27017\"}, {_id: 2, host: \"mongodb_cfg3:27017\"}]})"; do
    echo "Ожидаем готовности конфигурации сервера..."
    sleep 5
done

until mongosh --host mongodb_sh1 --eval "rs.initiate({_id: \"mongoshard1\", members: [{_id: 0, host: \"mongodb_sh1:27017\"}]})"; do
    echo "Ожидание готовности 1 шарда..."
    sleep 5
done

until mongosh --host mongodb_sh2 --eval "rs.initiate({_id: \"mongoshard2\", members: [{_id: 0, host: \"mongodb_sh2:27017\"}]})"; do
    echo "Ожидание готовности 2 шарда..."
    sleep 5
done

until mongosh --host mongodb_router --eval "sh.addShard(\"mongoshard1/mongodb_sh1\")"; do
    echo "Ожидание добавления к роутеру 1 шарда..."
    sleep 5
done

until mongosh --host mongodb_router --eval "sh.addShard(\"mongoshard2/mongodb_sh2\")"; do
    echo "Ожидание добавления к роутеру 2 шарда..."
    sleep 5
done

mongosh --host mongodb_router --eval "sh.status()"

mongosh mongodb_router:27017/${DB_NAME} --eval "sh.enableSharding('${DB_NAME}')
    && db.createCollection('${REVIEW_COLL}')
    && db.createCollection('${BOOKMARK_COLL}')
    && db.createCollection('${REVIEWS_COLL}')
    && sh.shardCollection('${DB_NAME}.${REVIEW_COLL}', {'film_id': 'hashed'})
    && sh.shardCollection('${DB_NAME}.${BOOKMARK_COLL}', {'film_id': 'hashed'})
    && sh.shardCollection('${DB_NAME}.${REVIEWS_COLL}', {'film_id': 'hashed'})
    "

echo "Кластер успешно сконфигурирован"
