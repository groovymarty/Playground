# basic_data.phone

deletePunctTrans = str.maketrans("", "", "-() ")
deleteNumTrans = str.maketrans("", "", "0123456789")

def check_phone(value):
    ucValue = value.strip().upper()
    if len(ucValue) == 0:
        return ""
    elif ucValue == "UNKNOWN":
        return "Unknown"
    else:
        # delete some punctuation
        nums = ucValue.translate(deletePunctTrans)
        # nothing left but numbers?
        if nums.translate(deleteNumTrans) == "":
            # yes, check for some common cases
            if len(nums) == 7:
                return "{}-{}".format(nums[0:3], nums[3:7])
            elif len(nums) == 10:
                return "({}) {}-{}".format(nums[0:3], nums[3:6], nums[6:10])
            elif len(nums) == 11 and nums[0] == "1":
                return "1-{}-{}-{}".format(nums[1:4], nums[4:7], nums[7:11])
        # otherwise return string unchanged
        return value
