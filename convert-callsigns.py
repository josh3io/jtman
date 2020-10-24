
import csv
import pickle

callstate={}
with open('call_state.dat') as fin:
    reader=csv.reader(fin, skipinitialspace=True, delimiter='|', quotechar="'")
    for row in reader:
        #print (row[0])
        callstate[row[0]]=row[1:]
print ('Done')




print ("Saving Object")
# Step 2
with open('callstate.dictionary', 'wb') as callstate_dictionary_file:
 
  # Step 3
  pickle.dump(callstate, callstate_dictionary_file)


#def save_obj(obj, name ):
#    with open('obj/'+ name + '.pkl', 'wb') as f:
#        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
#
#def load_obj(name ):
#    with open('obj/' + name + '.pkl', 'rb') as f:
#        return pickle.load(f)


print (callstate["N3KA"])
print (callstate["N3LGA"])
print (callstate["WA6SM"])
