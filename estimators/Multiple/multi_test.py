import json
import numpy as np
import pandas as pd
from keras.models import model_from_json
from multiAD import RLenv
import matplotlib.pyplot as plt


if __name__ == "__main__":
    batch_size = 10
    test_path = '../../datasets/corrected'

    with open("models/multi_model.json", "r") as jfile:
        model = model_from_json(json.load(jfile))
    model.load_weights("models/multi_model.h5")
    model.compile("sgd", "mse")

    # Define environment, game, make sure the batch_size is the same in train
    env = RLenv(test_path,'test',batch_size)
    

    total_reward = 0    
    epochs = int(env.data_shape[0]/env.batch_size)
    
    
    true_labels = np.zeros(len(env.attack_names))
    estimated_labels = np.zeros(len(env.attack_names),dtype=int)
    estimated_correct_labels = np.zeros(len(env.attack_names),dtype=int)
    
    for e in range(epochs):
        #states , labels = env.get_sequential_batch(test_path,batch_size = env.batch_size)
        states , labels = env.get_batch(batch_size = env.batch_size)
        q = model.predict(states)
        actions = np.argmax(q,axis=1)        
        
        reward = np.zeros(env.batch_size)
        
        true_labels += np.sum(labels).values

        for indx,a in enumerate(actions):
            estimated_labels[a] +=1              
            if a == np.argmax(labels.iloc[indx].values):
                reward[indx] = 1
                estimated_correct_labels[a] += 1
        
        
        total_reward += int(sum(reward))
        print("\rEpoch {}/{} | Tot Rew -- > {}".format(e,epochs,total_reward), end="")
        
    Accuracy = np.nan_to_num(estimated_correct_labels / true_labels )
    Mismatch = abs(estimated_correct_labels - true_labels)+abs(estimated_labels-estimated_correct_labels)
    print('\r\nTotal reward: {} | Number of samples: {} | Accuracy = {}%'.format(total_reward,
          int(epochs*env.batch_size),float(100*total_reward/(epochs*env.batch_size))))
    outputs_df = pd.DataFrame(index = env.attack_names,columns = ["Estimated","Correct","Total","Acuracy","Mismatch"])
    for indx,att in enumerate(env.attack_names):
       outputs_df.iloc[indx].Estimated = estimated_labels[indx]
       outputs_df.iloc[indx].Correct = estimated_correct_labels[indx]
       outputs_df.iloc[indx].Total = true_labels[indx]
       outputs_df.iloc[indx].Mismatch = abs(Mismatch[indx])
       outputs_df.iloc[indx].Acuracy = Accuracy[indx]*100

        
    print(outputs_df)
    
    #%%
    
    ind = np.arange(1,len(env.attack_names)+1)
    fig, ax = plt.subplots()
    width = 0.35
    p1 = plt.bar(ind, estimated_correct_labels,width,color='g')
    p2 = plt.bar(ind, 
                 (np.abs(estimated_correct_labels-true_labels)\
                  +np.abs(estimated_labels-estimated_correct_labels)),width,
                 bottom=estimated_correct_labels,color='r')

    
    ax.set_xticks(ind)
    ax.set_xticklabels(env.attack_names,rotation='vertical')
    ax.set_yscale('log')

    #ax.set_ylim([0, 100])
    ax.set_title('Test set scores')
    plt.legend((p1[0], p2[0]), ('Correct estimated', 'Incorrect estimated'))
    plt.tight_layout()
    #plt.show()
    plt.savefig('results/test_multi_log.eps', format='eps', dpi=1000)

