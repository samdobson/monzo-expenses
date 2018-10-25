# :credit_card: Monzo Expenses

Beautiful expense reports direct from your Monzo Account.

Pulls all transactions categorised as 'Expenses' within a specified time range along with any notes you have made.

[![Expense Report](https://raw.githubusercontent.com/samdobson/monzo-expenses/master/example.png)](https://github.com/samdobson/monzo-expenses/blob/master/example.pdf)

## Installation

Monzo Expenses is built with Python and requires version 3.7.

```python
pip install monzo-expenses
```

Running Linux? That's all you need!

Windows users will also need to install GTK. The [64-bit](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/download/2018-10-03/gtk3-runtime-3.24.1-2018-10-03-ts-win64.exe) install is a couple of clicks. 32-bit is [another story](https://weasyprint.readthedocs.io/en/latest/install.html#msys2-gtk) (don't you just love software?)

MacOS folks can try the following (untested):

```
brew install cairo pango gdk-pixbuf libff
```

## Usage

```bash
$ monzo-expenses --from 01-09-18 --to 30-09-18 --output my_september_expenses.pdf
```

On the first run you will be prompted to register the application and authorise access to your Monzo account.

## :lock: Security

Monzo Expenses runs on your local machine. It is your responsibility to secure access to the software.

The Monzo API does not allow movement of money (other than into/out of pots).

Please do not open a GitHub issue for security-related matters - use this [contact form](https://fncontact.com/monzo-coffee) to contact the author.

## :green_book: Documentation

For more information, please consult the [documentation](https://monzo-expenses.readthedocs.io/en/latest/).

Support is provided on a best-efforts basis.
