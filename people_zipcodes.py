from marshmallow import Schema, fields, post_load, missing
from faker import Factory

from collections import defaultdict
import pprint

fake = Factory.create()

class Person:
    def __init__(self, name, zipcode):
        self.name = name
        self.zipcode = zipcode

    def __repr__(self):
        return "Person(name={0}, zipcode={1})".format(self.name, self.zipcode)

    def __eq__(self, other):
        return other.name == self.name and other.zipcode == self.zipcode

    def __hash__(self):
        return hash(frozenset([self.name, self.zipcode]))


class PersonSchema(Schema):
    name = fields.Str()
    zipcode = fields.Str()

    @post_load
    def make_person(self, data):
        instance = Person.__new__(Person)
        instance.__dict__.update(data)
        return instance


class PeopleIndex:

    def __init__(self, city_zips, people):
        self.people_index = defaultdict(set)
        self.generate_people_index(city_zips, people)

    def generate_people_index(self, city_zips, people):
        for person in people:
            pz = person.zipcode
            for city, zipcodes in city_zips.items():
                for zipcode in zipcodes:
                    if zipcode == pz:
                        self.people_index[city].add(person)

    def __repr__(self):
        return "PeopleIndex({0})".format(self.people_index)

    def __eq__(self, other):
        if self is other:
            return True
        return self.people_index == other.people_index

# Example PeopleIndex
# -----------------------------------------------------------
# Requirement:  The cities and people are unknown until run-time
#
# {'Cupertino': {Person(name=Anthony Dube, zipcode=95116),
#                Person(name=Elsie Austin, zipcode=95113),
#                Person(name=Tammy Mention, zipcode=95117),
#                Person(name=Robert Cairns, zipcode=95014)},
#  'Los Altos': {Person(name=Lynn Lazenby, zipcode=95121),
#                Person(name=Harold White, zipcode=94022),
#                Person(name=Jordan Gomez, zipcode=95122),
#                Person(name=Stacy Cole, zipcode=95123)},
#  'Mountain View': {Person(name=Patrick Mcbride, zipcode=94041),
#                    Person(name=Nicki Woods, zipcode=94040)},
#  'Palo Alto': {Person(name=Cecil Arias, zipcode=94301),
#                Person(name=Claudia Stock, zipcode=94303)},
#  'San Jose': {Person(name=Vada Torres, zipcode=95111),
#               Person(name=Raymond Ellis, zipcode=95112),
#               Person(name=Jerry Mitchell, zipcode=95110)},
#  'Santa Clara': {Person(name=Mary Valle, zipcode=95050),
#                  Person(name=Peggy Mabe, zipcode=95051),
#                  Person(name=Luke Higginbotham, zipcode=94043),

class CollectionDict(fields.Dict):

    def __init__(self, child, *args, **kwargs):
        self.child = child
        super().__init__(*args, **kwargs)

    @staticmethod
    def accessor(key, obj, default=missing):
        """Custom accessor that only handles list and tuples.
        """
        try:
            return obj[key]
        except IndexError:
            return default

    def _serialize(self, value, attr, obj):
        ret = super()._serialize(value, attr, obj)
        for key, collection in ret.items():
            lvalue = list(collection)
            ret[key] = [
                self.child.serialize(i, lvalue, accessor=self.accessor)
                for i in range(len(lvalue))
            ]
        return ret

    def _deserialize(self, value, attr, data):
        ret = super()._deserialize(value, attr, data)
        for key, collection in value.items():
            ret[key] = set([
                self.child.deserialize(each, i, collection)
                for i, each in enumerate(collection)
            ])
        return ret


class PeopleIndexSchema(Schema):
    people_index = CollectionDict(fields.Nested(PersonSchema()))

    @post_load
    def make_peopleindex(self, data):
        instance = PeopleIndex.__new__(PeopleIndex)
        instance.__dict__.update(data)
        return instance


def main():

    city_zips = {'San Jose': ['95110', '95111', '95112'],
                 'Cupertino': ['95014', '95113', '95116', '95117'],
                 'Los Altos': ['94022', '95121', '95122', '95123'],
                 'Mountain View': ['94040', '94041'],
                 'Santa Clara': ['95050', '95051', '95054', '94043'],
                 'Palo Alto': ['94301', '94303']}

    people = []
    for city, zips in city_zips.items():
        for zipcode in zips:
            people.append(Person(name=fake.name(), zipcode=zipcode))

    people_index = PeopleIndex(city_zips, people)

    schema = PeopleIndexSchema()

    dump_data = schema.dump(people_index).data

    pp = pprint.PrettyPrinter(indent=1)
    print('='*25,'SERIALIZED', '='*25)
    pp.pprint(dump_data)

    load_data = schema.load(dump_data).data

    print('\n', '='*25,'DE-SERIALIZED', '='*25)
    pp.pprint(load_data)

    print('\n\n', 'Deserialized Equals Original:  ', load_data == people_index)

if __name__ == "__main__":
    main()
