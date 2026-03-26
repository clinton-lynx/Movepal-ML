from model import train_model


if __name__ == '__main__':
    result = train_model()
    print(f"Rows used: {result['rows']}")
    print(f"Accuracy: {result['accuracy'] * 100:.2f}%")
    print(result['report'])
