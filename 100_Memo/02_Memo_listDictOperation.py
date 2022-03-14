myList = [2 ,3, 4, 5, 6];
print(type(myList));
# <type 'list'>


k = [a+4 for a in myList];
print(k)
# [6, 7, 8, 9, 10]

a_dict = {'color': 'blue', 'fruit': 'apple', 'pet': 'dog'}
d_items = a_dict.items()
print(d_items)
# [('color', 'blue'), ('pet', 'dog'), ('fruit', 'apple')]

# https://docs.python.org/3/reference/expressions.html#membership-test-details
# in, not in 
print(3 in myList); # true


#https://realpython.com/iterate-through-dictionary-python/#using-comprehensions
#  dictionary comprehension (for in zip)
objects = ['blue', 'apple', 'dog']
categories = ['color', 'fruit', 'pet']
a_dict = {key: value for key, value in zip(categories, objects)}
print(a_dict) # {'color': 'blue', 'pet': 'dog', 'fruit': 'apple'}
objects[1] = "hellow";
print(a_dict) # {'color': 'blue', 'pet': 'dog', 'fruit': 'apple'}


objects = ['blue', 'apple', 'dog']
categories = ['color', 'fruit', 'pet']
a = zip(categories, objects)
print(a)
#[('color', 'blue'), ('fruit', 'apple'), ('pet', 'dog')]


#https://realpython.com/list-comprehension-python/#using-map-objects
# list map
txns = [1.09, 23.56, 57.84, 4.56, 6.78]
TAX_RATE = .08
def get_price_with_tax(txn):
    return txn * (1 + TAX_RATE)
final_prices = map(get_price_with_tax, txns)
list(final_prices)
#[1.1772000000000002, 25.4448, 62.467200000000005, 4.9248, 7.322400000000001]
# 1.09*(1+0.08)

#https://realpython.com/list-comprehension-python/#using-list-comprehensions
txns = [1.09, 23.56, 57.84, 4.56, 6.78]
TAX_RATE = .08
def get_price_with_tax(txn):
    return txn * (1 + TAX_RATE)
final_prices = [get_price_with_tax(i) for i in txns]
final_prices
#[1.1772000000000002, 25.4448, 62.467200000000005, 4.9248, 7.322400000000001]

#https://realpython.com/list-comprehension-python/#how-to-supercharge-your-comprehensions
sentence = 'The rocket, who was named Ted, came back from Mars because he missed his friends.'
def is_consonant(letter):
    vowels = 'aeiou'
    return letter.isalpha() and letter.lower() not in vowels
consonants = [i for i in sentence if is_consonant(i)]
['T', 'h', 'r', 'c', 'k', 't', 'w', 'h', 'w', 's', 'n', 'm', 'd', \
'T', 'd', 'c', 'm', 'b', 'c', 'k', 'f', 'r', 'm', 'M', 'r', 's', 'b', \
'c', 's', 'h', 'm', 's', 's', 'd', 'h', 's', 'f', 'r', 'n', 'd', 's']

#https://realpython.com/list-comprehension-python/#using-conditional-logic
original_prices = [1.25, -9.45, 10.22, 3.78, -5.92, 1.16]
prices = [i*2 if i > 0 else 0 for i in original_prices]
print(prices)
#[2.5, 0, 20.44, 7.56, 0, 2.32]


#https://realpython.com/python-sets/
a=[i for i in range(100000000)];
k = [i for i in range(100000000)]
b=set(k);

print(9999999999 in a)
print(9999999999 in b) # more fast !!

