import unittest
import embutils

embeddings_filename = "/srv/data/word2vec/GoogleNews-vectors-negative300.bin"
cutoff = 100000

class ResultAssert:
    def assert_results_almost_equal(self, res1, res2):
        self.assertEqual(len(res1), len(res2))
        for i in range(len(res1)):
            w1, s1 = res1[i]
            w2, s2 = res2[i]
            self.assertEqual(w1, w2)
            self.assertAlmostEqual(s1, s2, places=5)

class BasicLikeUnlike(ResultAssert, unittest.TestCase):
    def setUp(self):
        self.embs = embutils.WordEmbeddings()
        self.embs.load_from_file(embeddings_filename, cutoff)
#        print(self.embs.like("cat", "dog", "hamster"))
    def test_one_arg(self):
        correct = (('lazy', 5.960464477539063e-08),
                   ('laziness', 0.4148856997489929),
                   ('slackers', 0.4356740117073059),
                   ('stupid', 0.4442487955093384),
                   ('dopey', 0.45400428771972656),
                   ('dumb', 0.4593202471733093),
                   ('self_indulgent', 0.46173417568206787),
                   ('tired', 0.4708591103553772),
                   ('cranky', 0.47928082942962646),
                   ('brainless', 0.48132115602493286))
        self.assert_results_almost_equal(self.embs.like("lazy"), correct)
    def test_two_args_like(self):
        correct = (('cool', 0.0),
                   ('neat', 0.0),
                   ('nice', 0.3126871585845947),
                   ('awesome', 0.4206209182739258),
                   ('weird', 0.4324718117713928),
                   ('lovely', 0.434161901473999),
                   ('classy', 0.44367116689682007),
                   ('coolest', 0.44841432571411133),
                   ('Cool', 0.4490888714790344),
                   ('cute', 0.45029717683792114))
        self.assert_results_almost_equal(self.embs.like("cool", "neat"), correct)
    def test_three_args_like(self):
        correct = (('mouse', 0),
                   ('keyboard', 0),
                   ('keyboards', 0.160486),
                   ('stylus', 0.224258),
                   ('Keyboard', 0.225979),
                   ('trackpad', 0.251766),
                   ('Wiimote', 0.297133),
                   ('joystick', 0.299078),
                   ('touchpad', 0.299386),
                   ('keypad', 0.317311))
        like_args = embutils.LikeArgs(embutils.LikeArgs("mouse", "keyboard", False), embutils.LikeArgs("screen"), True)
        self.assert_results_almost_equal(self.embs.like(like_args), correct)

        
if __name__ == '__main__':
    unittest.main()
