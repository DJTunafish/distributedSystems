def compareMsgId(item1, item2):
    tmp1 = item1.split('-')
    tmp2 = item2.split('-')
    print("Print")
    if int(tmp1[0]) != int(tmp2[0]):
        print("First case")
        return int(tmp1[0]) - int(tmp2[0])
    else:
        print("Here")
        print(tmp1[1])
        print(tmp2[1])
        return int(tmp1[1]) - int(tmp2[1])



print(sorted(['2-2', '2-1', '2-3'], cmp=compareMsgId))
