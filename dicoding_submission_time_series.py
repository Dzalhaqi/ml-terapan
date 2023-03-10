# -*- coding: utf-8 -*-
"""dicoding-submission-time-series.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_73sEg4kfuYRjzGYAFoZSg9thBK5MIlR

# Time Series Delhi Weather Data

## Download dataset from Kaggle
"""

# install kaggle package
from sklearn.model_selection import train_test_split
from keras.layers import Dense, LSTM
import tensorflow as tf
import matplotlib.pyplot as plt
import pandas as pd
!pip install - q kaggle

# make directory and change permission
!mkdir - p ~/.kaggle
!cp kaggle.json ~/.kaggle/
!chmod 600 ~/.kaggle/kaggle.json
!ls ~/.kaggle

# test kaggle dataset list
!kaggle datasets list

# download dataset, choose 'copy api command' from kaggle dataset
!kaggle datasets download - d mahirkukreja/delhi-weather-data

# unzip
!mkdir delhi-weather-data
!unzip delhi-weather-data.zip - d delhi-weather-data
!ls delhi-weather-data

"""## Load dataset"""

# load dataset
df = pd.read_csv('delhi-weather-data/testset.csv')
df.head(10)

# total data
df.shape

# data info
df.info()

# null check
df.isnull().sum()

df['datetime_utc'] = pd.to_datetime(df['datetime_utc'])
df['datetime_utc'].head()
# we will fill the null row
df[' _tempm'].fillna(df[' _tempm'].mean(), inplace=True)
df = df[['datetime_utc', ' _tempm']]
df.head()

df.info()

"""## Model & Plot"""

delhi = df[['datetime_utc', ' _tempm']].copy()
delhi['just_date'] = delhi['datetime_utc'].dt.date

delhifinal = delhi.drop('datetime_utc', axis=1)
delhifinal.set_index('just_date', inplace=True)
delhifinal.head()

delhifinal.info()


plt.figure(figsize=(20, 8))
plt.plot(delhifinal)
plt.title('Delhi Weather')
plt.xlabel('Date')
plt.ylabel('temperature')
plt.show()

# get data values
date = df['datetime_utc'].values
temp = df[' _tempm'].values


def windowed_dataset(series, window_size, batch_size, shuffle_buffer):
    series = tf.expand_dims(series, axis=-1)
    ds = tf.data.Dataset.from_tensor_slices(series)
    ds = ds.window(window_size + 1, shift=1, drop_remainder=True)
    ds = ds.flat_map(lambda w: w.batch(window_size + 1))
    ds = ds.shuffle(shuffle_buffer)
    ds = ds.map(lambda w: (w[:-1], w[-1:]))
    return ds.batch(batch_size).prefetch(1)


x_train, x_test, y_train, y_test = train_test_split(
    temp, date, test_size=0.2, random_state=0, shuffle=False)
print(len(x_train), len(x_test))

# model

data_x_train = windowed_dataset(
    x_train, window_size=60, batch_size=100, shuffle_buffer=5000)
data_x_test = windowed_dataset(
    x_test, window_size=60, batch_size=100, shuffle_buffer=5000)

model = tf.keras.models.Sequential([
    tf.keras.layers.Conv1D(filters=32, kernel_size=5,
                           strides=1, padding="causal",
                           activation="relu",
                           input_shape=[None, 1]),
    tf.keras.layers.LSTM(64, return_sequences=True),
    tf.keras.layers.LSTM(64, return_sequences=True),
    tf.keras.layers.Dense(30, activation="relu"),
    tf.keras.layers.Dense(10, activation="relu"),
    tf.keras.layers.Dense(1),
    tf.keras.layers.Lambda(lambda x: x * 400)
])

lr_schedule = tf.keras.callbacks.LearningRateScheduler(
    lambda epoch: 1e-8 * 10**(epoch / 20))
optimizer = tf.keras.optimizers.SGD(lr=1e-8, momentum=0.9)
model.compile(loss=tf.keras.losses.Huber(),
              optimizer=optimizer,
              metrics=["mae"])

max = df[' _tempm'].max()
print('Max value : ')
print(max)

min = df[' _tempm'].min()
print('Min Value : ')
print(min)

x = (90.0 - 1.0) * (10 / 100)
print(x)

# callback


class myCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs={}):
        if(logs.get('mae') < x):
            self.model.stop_training = True
            print("\nMAE of the model < 10% of data scale")


callbacks = myCallback()

tf.keras.backend.set_floatx('float64')
history = model.fit(data_x_train, epochs=500,
                    validation_data=data_x_test, callbacks=[callbacks])

# plot of mae
plt.plot(history.history['mae'])
plt.plot(history.history['val_mae'])
plt.title('MAE')
plt.ylabel('mae')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()

# plot of loss
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model Loss')
plt.ylabel('loss')
plt.xlabel('epoch')
plt.legend(['train', 'test'], loc='upper left')
plt.show()
