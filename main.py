import re
from collections import UserDict
from datetime import datetime
from datetime import date
import shelve
import pickle


class Field:
    def __init__(self, value) -> None:
        self.value = value

    def __str__(self) -> str:
        return f'{self.value}'


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value) -> None:
        super().__init__(value)
        self.__value = None
        self.value = value

    @property
    def value(self) -> str:
        return self.__value

    @value.setter
    def value(self, value) -> None:
        if value.isdigit():
            self.__value = value


class Birthday(Field):
    def __init__(self, value) -> None:
        super().__init__(value)
        self.__value = None
        self.value = value

    @property
    def value(self) -> str:
        return self.__value

    @value.setter
    def value(self, value) -> None:
        if value:
            try:
                datetime.strptime(value, "%d.%m.%Y")
            except ValueError:
                raise ValueError("Incorrect data format, should be DD.MM.YYYY")
        self.__value = value


class Record:
    def __init__(self, name: Name, phones=[], birthday: Birthday = None) -> None:
        self.name = name
        self.phone_list = phones
        self.birthday = birthday

    def __str__(self) -> str:
        return f'User {self.name} - Phones: {", ".join([phone.value for phone in self.phone_list])}' \
               f' - Birthday: {self.birthday} '

    def add_phone(self, phone: Phone) -> None:
        self.phone_list.append(phone)

    def del_phone(self, phone: Phone) -> None:
        self.phone_list.remove(phone)

    def edit_phone(self, phone: Phone, new_phone: Phone) -> None:
        self.phone_list.remove(phone)
        self.phone_list.append(new_phone)

    def days_to_birthday(self):
        if self.birthday:
            start = date.today()
            birthday_date = datetime.strptime(str(self.birthday), '%d.%m.%Y')
            end = date(year=start.year, month=birthday_date.month,
                       day=birthday_date.day)
            count_days = (end - start).days
            if count_days < 0:
                count_days += 365
            return count_days
        else:
            return 'Unknown birthday'


class AddressBook(UserDict):
    def __init__(self):
        super().__init__()
        self.n = None

    def add_record(self, record: Record) -> None:
        self.data[record.name.value] = record

    def iterator(self, n=2, days=0):
        self.n = n
        index = 1
        print_block = '-' * 50 + '\n'
        for record in self.data.values():
            if days == 0 or (record.birthday.value is not None and record.days_to_birthday(record.birthday) <= days):
                print_block += str(record) + '\n'
                if index < n:
                    index += 1
                else:
                    yield print_block
                    index, print_block = 1, '-' * 50 + '\n'
        yield print_block


class InputError:
    def __init__(self, func) -> None:
        self.func = func

    def __call__(self, contacts, *args):
        try:
            return self.func(contacts, *args)
        except IndexError:
            return 'Sorry,enter command,name,phone!'
        except KeyError:
            return 'Sorry,user not found, try again!'
        except ValueError:
            return 'Sorry,phone number not found,try again!'


def greeting(*args):
    return 'Hello! Can I help you?'


@InputError
def add(contacts, *args):
    name = Name(args[0])
    phone = Phone(args[1])
    try:
        birthday = Birthday(args[2])
    except IndexError:
        birthday = None
    if name.value in contacts:
        contacts[name.value].add_phone(phone)
        writing_db(contacts)
        return f'Add phone number: {phone} for {name}'
    else:
        contacts[name.value] = Record(name, [phone], birthday)
        writing_db(contacts)
        return f'Add {name}: {phone}'


@InputError
def change(contacts, *args):
    name, old_phone, new_phone = args[0], args[1], args[2]
    contacts[name].edit_phone(Phone(old_phone), Phone(new_phone))
    writing_db(contacts)
    return f'{name} your old phone number: {old_phone} was changed to {new_phone}'


@InputError
def phone(contacts, *args):
    name = args[0]
    phone = contacts[name]
    return f'{phone}'


@InputError
def del_phone(contacts, *args):
    name, phone = args[0], args[1]
    contacts[name].del_phone(Phone(phone))
    writing_db(contacts)
    return f'for {name},phone:{phone} is delete'


def show_all(contacts, *args):
    if not contacts:
        return 'Address book is empty'
    result = 'Users: \n'
    print_list = contacts.iterator()
    for item in print_list:
        result += f'{item}'
    return result


def birthday(contacts, *args):
    if args:
        name = args[0]
        return f'{contacts[name].birthday}'


def show_birthday_30_days(contacts, *args):
    result = 'List of users with birthday in 30 days:'
    for key in contacts:
        if contacts[key].days_to_birthday() <= 30:
            result += f'\n{contacts[key]}'
    return result


def exiting(*args):
    return 'Good bye!'


def unknown_command(*args):
    return 'Unknown command! Enter again!'


file_name = 'AddressBook.bin'


def reading_db(file_name):
    with open(file_name, "rb") as fh:
        try:
            unpacked = pickle.load(fh)
        except EOFError:
            unpacked = AddressBook()
        return unpacked


def writing_db(contacts):
    with open(file_name, "wb") as fh:
        pickle.dump(contacts, fh)


@InputError
def find(contacts, *args):
    args_str = ''
    for i in args:
        args_str += i + ' '
    user_request = '[' + args_str.lower()[:-1] + ']{2,}'
    reg_exp = fr'{user_request}'
    result = f'List with matches:\n'
    for value in contacts.values():
        match = re.findall(reg_exp, str(value).lower())
        if str(value).find(str(match)) and len(match):
            result += f'{str(value)}'+'\n'
    return result


COMMANDS = {greeting: ['hello'], add: ['add '], change: ['change '], phone: ['phone '],
            show_all: ['show all'], exiting: ['good bye', 'close', 'exit'],
            del_phone: ['delete '], birthday: ['birthday '], show_birthday_30_days: ['soon birthday'],
            find: ['find', 'check']}


def new_func():
    return (str, list)


def command_parser(user_command: str) -> new_func():
    for key, list_value in COMMANDS.items():
        for value in list_value:
            if user_command.lower().startswith(value):
                args = user_command[len(value):].split()
                return key, args
    else:
        return unknown_command, []


def main():
    contacts = reading_db(file_name)
    while True:
        user_command = input('>>> ')
        command, data = command_parser(user_command)
        print(command(contacts, *data))
        if command is exiting:
            break


if __name__ == '__main__':
    main()
