"""
Implements the *PositionRank* algorithm.
"""

import typing
from .base import BaseTextRank, Lemma
from .util import groupby_apply


class PositionRank (BaseTextRank):
    """
Implements the *PositionRank* algorithm described by
[[florescuc17]](https://derwen.ai/docs/ptr/biblio/#florescuc17),
deployed as a `spaCy` pipeline component.
    """

    def get_personalization (
        self
        ) -> typing.Optional[typing.Dict[Lemma, float]]:
        """
Get the *node weights* for initializing the use of the
[*Personalized PageRank*](https://derwen.ai/docs/ptr/glossary/#personalized-pagerank)
algorithm.

From the cited reference:

> Specifically, we propose to assign a higher probability to a word
> found on the 2nd position as compared with a word found on the 50th
> position in the same document. The weight of each candidate word is
> equal to its inverse position in the document.  If the same word
> appears multiple times in the target document, then we sum all its
> position weights.

> For example, a word v_i occurring in the following positions: 2nd,
> 5th and 10th, has a weight p(v_i) = 1/2 + 1/5 + 1/10 = 4/5 = 0.8
> The weights of words are normalized before they are used in the
> position-biased PageRank.

    returns:
Biased restart probabilities to use in the *PageRank* algorithm.
        """
        weighted_tokens: typing.List[typing.Tuple[str, float]] = [
            (tok, 1 / (i + 1))
            for i, tok in enumerate(
                token.lemma_ for token in self.doc if token.pos_ in self.pos_kept
            )
        ]

        keyfunc = lambda x: x[0]
        applyfunc = lambda g: sum(w for text, w in g)

        accumulated_weighted_tokens: typing.List[typing.Tuple[str, float]] = groupby_apply(
            weighted_tokens,
            keyfunc,
            applyfunc,
        )

        accumulated_weighted_tokens = sorted(
            accumulated_weighted_tokens, key=lambda x: x[1]
        )

        norm_weighted_tokens = {
            k: w / sum(w_ for _, w_ in accumulated_weighted_tokens)
            for k, w in accumulated_weighted_tokens
        }

        weighted_nodes = {
            # while the authors assign higher probability to a "word",
            # our *lemma graph* vertices are (lemma, pos) tuples,
            # therefore we map each `Lemma` weight to all the *lemma
            # graph* vertices which contain it
            # TODO: should this map to (lemma, pos) pairs instead?
            Lemma(token.lemma_, token.pos_): norm_weighted_tokens[token.lemma_]
            for token in self.doc
            if token.pos_ in self.pos_kept
        }

        return weighted_nodes
