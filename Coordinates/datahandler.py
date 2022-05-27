from datetime import datetime, timedelta

def datahandler(path, delay):

    previous = ''
    new = []

    with open(f'{path}\goals.txt', 'r') as file:
        for line in file:
            if previous=='':
                new.append(line)
                previous=line
            if line!=previous and datetime.strptime(line, "%H:%M:%S ") > datetime.strptime(previous, "%H:%M:%S ") + timedelta(seconds=delay):
                new.append(line)
                previous = line
        file.close()

    with open(f'{path}\goals.txt', "w") as file:
        for line in new:
            file.write(line)
        file.close()