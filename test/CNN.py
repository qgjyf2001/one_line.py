from keras import layers
from keras.models import Sequential
def build_model():
    model = Sequential()
    model.add(layers.Conv2D(32, (3, 3), input_shape=(28, 28, 1)))
    model.add(layers.PReLU('ones'))
    model.add(layers.MaxPool2D(pool_size=(10, 10), strides=(1, 1)))
    model.add(layers.Conv2D(64, (5, 5)))
    model.add(layers.PReLU('ones'))
    model.add(layers.MaxPool2D(pool_size=(3, 3), strides=(1, 1)))
    model.add(layers.Conv2D(64, (3, 3)))
    model.add(layers.PReLU('ones'))
    model.add(layers.MaxPool2D(pool_size=(3, 3), strides=(1, 1)))
    model.add(layers.Flatten())
    model.add(layers.Dense(32, activation='relu'))
    model.add(layers.Dense(10, activation='softmax'))
    return model
model = build_model()
model.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])

from keras.datasets import mnist
from keras.utils import to_categorical

train, test  = mnist.load_data()
train_imgs, train_labels =train

test_imgs, test_labels = test
train_imgs = train_imgs / 255
test_imgs = test_imgs / 255
train_imgs = train_imgs.reshape(-1, 28, 28, 1)
test_imgs = test_imgs.reshape(-1, 28, 28, 1)
train_labels = to_categorical(train_labels)
test_labels = to_categorical(test_labels)
history = model.fit(train_imgs, train_labels, epochs=1, batch_size=64)
evaluate_res = model.evaluate(x=test_imgs, y=test_labels, batch_size=64)

print(evaluate_res)
