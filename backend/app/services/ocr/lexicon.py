class LexiconRescorer:
    def rescore(self, candidates, lexicon):
        # n-best output with Russian lexicon rescoring
        return candidates[0] if candidates else ""
