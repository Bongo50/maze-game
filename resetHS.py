import pickle

try:
    HSFile = open("highscore.pickle", "xb")
    pickle.dump(0, HSFile)
    HSFile.close()
except:
    HSFile = open("highscore.pickle", "wb")
    pickle.dump(0, HSFile)
    HSFile.close()