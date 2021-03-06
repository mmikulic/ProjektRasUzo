import sys
import numpy as np
import cv2 as cv
import getopt

import preproc
import classifier
import granlund
import get_silhouette

def help():
    """Outputs help string.
    """

    buff = "main.py [options]\n"
    buff += "Default values, if any, are given in square brackets. []\n"
    buff += "Required parameters:\n"
    buff += "--path=<path_to_data> --path to learning data\n"
    buff += "--method =<hu>|<granlund> --method for feature extraction\n"
    buff += "--threshold required if optparam is not set\n"
    buff += "##################################\n"

    buff += "Optional parameters (all other):\n"
    buff += "--optparam=0|1 -- if this option is selected, thresholds are read for every picture and --threshold is ignored, if set. [0]\n"
    buff += "##################################\n"

    buff += "Extraction related parameters:\n"
    buff += "--approach=c|g -- regulates whether colored pictures are compared or gray-scaled ones when extracting silhouettes. [c]\n"
    buff += "--threshtype=m|a -- regulates whether median or mean are used ase threshold types for getting black and white pictures.[m]\n"
    buff += "##################################"

    buff += "KNN-related parameters:\n"
    buff += "--nmax=<number> -- maximum number of neighbors for KNN classifier. [32]\n"
    buff += "--nclass=<number> -- number of neighbors used for classifying a picture. <= nmax. [7]\n"
    buff += "Be careful: setting nmax and not setting nclass could lead to errors if nmax is < 7 which"
    buff += "is the default nclass.\n"
    buff += "##################################\n"

    buff += "Random trees related parameters:\n"
    buff += "--maxdepth=<number> -- max depth of a random tree. [4]\n"
    buff += "--criteria=0=cv.TERM_CRITERIA_MAX_ITER|1=cv.TERM_CRITERIA_EPS|2=both -- termination criteria for random trees learning. [2]\n"
    buff += "--maxtrees=<number> -- maximum number of trees. [10]\n"
    buff += "--maxerror=<numer> -- if --criteria includes EPS part, this regulates max error allowed before stopping. [0.1]\n"
    buff += "##################################\n"

    print buff

def get_arguments(argv):
    """Uses getopt to get program parameters.
    """

    params = dict()
    try:
        opts, args = getopt.getopt(argv,"",["path=","threshold=","method=","optparam=","approach=", \
            "threshtype=","nmax=","nclass=","maxdepth=", "criteria=", "maxtrees=", "maxerror="])
    except getopt.GetoptError:
        help()
        sys.exit(1)
        # print ('main.py --path=<path_to_data> --method=<hu>|<granlund>  --threshold=<floating_point_number> --parameters=<0>|<1>')

    params["path"] = None
    params["threshold"] = None
    params["method"] = None
    params["param_flag"] = None

    for opt, arg in opts:
        # print (opt)
        if opt == '-h':
            # print ('main.py --method=<hu>|<granlund>  --threshold=<floating_point_number>')
            help()
            sys.exit(1)

        elif opt == "--threshold":
            params["threshold"] = float(arg)

        elif opt == "--method":
            if arg == "hu":
                params["method"] = 1
                # print ("here")
            elif arg == "granlund":
                params["method"] = 0
            # method = arg

        elif opt == "--path":
            params["path"] = arg

        elif opt == "--optparam":
            params["param_flag"] = int(arg)

        elif opt == "--approach":
            params["approach"] = arg
            # print (arg)

        elif opt == "--threshtype":
            params["threshtype"] == arg

        elif opt == "--nmax":
            params["nmax"] = int(arg)

        elif opt == "--nclass":
            params["nclass"] = int(arg)

        elif opt == "--maxdepth":
            params["maxdepth"] = int(arg)

        elif opt == "--criteria":
            if int(arg) == 0:
                params["criteria"] = cv.TERM_CRITERIA_MAX_ITER
            elif int(arg) == 1:
                params["criteria"] = cv.TERM_CRITERIA_EPS
            elif int(arg) == 2:
                params["criteria"] = cv.TERM_CRITERIA_MAX_ITER+cv.TERM_CRITERIA_EPS

        elif opt == "--maxtrees":
            params["maxtrees"] = int(arg)

        elif opt == "--maxerror":
            params["maxerror"] = float(arg)

    return params

def train(params):
    """Given a path to the pictures, trains all possible classifiers.
    """

    path = params["path"]
    threshold = params["threshold"]
    method = params["method"]
    if "param_flag" in params:
        param_flag = params["param_flag"]

    bayes = classifier.NormalBayes()
    knn = classifier.KNN()
    tree = classifier.RandomTrees()

    dataset, responses, decode = preproc.prepare_dataset_cv(path, threshold, method, param_flag, params)
    bayes.train(dataset, responses)
    knn.train(dataset, responses, params)
    tree.train(dataset, responses, params)

    return bayes, knn, tree, decode

def predict(bayes, knn, tree, decode, params):
    """Accepts trained classifiers and decode dictionary. Waits for a path to a picture to classify.
    """

    path = params["path"]
    threshold_ = params["threshold"]
    method_ = params["method"]
    if "param_flag" in params:
        parameters = params["param_flag"]

    if "approach" in params:
        approach_ = params["approach"]
    else:
        approach_ = "c"
    # print decode
    N = 0
    bayes_correct = 0
    knn_correct = 0
    tree_correct = 0

    print ("Type in the path to a picture and its background. -1 to end.")
    print ("Optionally, you can also put parameters if you selected the option when running.")
    print

    while True:
        line = sys.stdin.readline()
        pic = line.split()[0]
        if pic == "-1":
            break
        class_ = line.strip().split()[1]

        line = sys.stdin.readline()
        back = line.strip()

        if parameters == 1:
            threshold_ = float(sys.stdin.readline().strip())

        image = granlund.load_image_from_file(pic)
        background = granlund.load_image_from_file(back)
        silh = get_silhouette.get_silhouette(image, background, threshold = threshold_, approach = approach_)
        # preproc.display_image(silh)
        features = granlund.get_features(silh, method=method_)

        bayes_res = decode[bayes.predict(features)[0]]
        knn_res = decode[knn.predict(features, params)[0]]
        tree_res = decode[tree.predict(features)[0]]

        N += 1
        if bayes_res == class_:
            bayes_correct += 1
        if knn_res == class_:
            knn_correct += 1
        if tree_res == class_:
            tree_correct += 1

        print ("Bayes result: " + bayes_res)
        print ("KNN result: " + knn_res)
        print ("Tree result: " + tree_res)

    print

    print("Correctness:")
    print("Bayes: %.5lf" % (bayes_correct / float(N)))
    print("KNN: %.5lf" % (knn_correct / float(N)))
    print("tree: %.5lf" % (tree_correct / float(N)))

if __name__ == "__main__":
    params = get_arguments(sys.argv[1:])

    if "path" not in params or "method" not in params:
        print ("Not enough arguments.")
        help()
        sys.exit(1)

    if "threshold" not in params:
        if "param_flag" not in params or params["param_flag"] == 0:
            print ("Not enough arguments.")
            help()
            sys.exit(1)

    bayes, knn, tree, decode, = train(params)
    predict(bayes, knn, tree, decode, params)
