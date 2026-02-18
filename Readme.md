# run these files in different terminals

1. termial 1  -OPTIONAL
cd C:\kafka
.\bin\windows\zookeeper-server-start.bat .\config\zookeeper.properties

2. terminal 2
cd C:\kafka
.\bin\windows\kafka-server-start.bat .\config\server.properties

# Start Redis server	
C:\Redis\redis-server.exe

# only if topic is not created 
3. terminal 3 - OPTIONAL
cd C:\kafka
.\bin\windows\kafka-topics.bat --create --topic transactions --bootstrap-server 127.0.0.1:9092 --partitions 1 --replication-factor 1

4.terminal 3
cd c:\Users\harsh\OneDrive\Desktop\Pythonnn\Pre-Delinquecy
python kafka\transaction_producer.py

5.terminal 4
cd c:\Users\harsh\OneDrive\Desktop\Pythonnn\Pre-Delinquecy
python kafka\transactions_consumer.py

6.terminal 5
cd c:\Users\harsh\OneDrive\Desktop\Pythonnn\Pre-Delinquecy
python features\feature_engine.py    

8. terminal 7
python risk\risk_engine.py

# to check redis is updating its data
cd C:\Users\harsh\OneDrive\Documents\Redis
.\redis-cli.exe
--{ writr -"ping" you should get response "pong" }
 in same termial type -> keys *
 to check updated value of customer -> hgetall customer:12

# install xgboost -> pip install xgboost scikit-learn joblib

