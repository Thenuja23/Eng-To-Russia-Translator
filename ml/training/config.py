class TrainingConfig:
    batch_size = 32
    epochs = 50
    lr = 0.001
    early_stopping_patience = 10
    img_height = 32
    img_width = 128
    max_text_len = 25
    charset = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    train_split = 0.8
    val_split = 0.1
    test_split = 0.1
    device = 'cpu'
