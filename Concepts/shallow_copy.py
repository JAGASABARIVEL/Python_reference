#!/usr/bin/python

object1 = [1, 2, 3]
object2 = object1

print "\n\nBEFORE MODIFYING OBJECT IN SHALLOW COPY ENVIRONMENT(PYTHON DEFAULT)"
print "object1 : ", object1, id(object1)
print "object2 : ", object2, id(object2)

object2[2] = 4

print "\n\nAFTER MODIFYING OBJECT IN SHALLOW COPY ENVIRONMENT"
print "object1 : ", object1
print "object2 : ", object2


object3 = []
for i in object1:
    object3.append(i)

print "\n\nBEFORE MODIFYING OBJECT IN DEEP COPY ENVIRONMENT"
print "object1 : ", object1, id(object1)
print "object3 : ", object3, id(object3)

object3[2] = 5

print "\n\nAFTER MODIFYING OBJECT IN DEEP COPY ENVIRONMENT"
print "object1 : ", object1
print "object3 : ", object3
