-- Copyright (C) 2014, Ugo Pozo
--               2014, Câmara Municipal de São Paulo

-- ParseUrl.hs - parser de URL em Haskell.

-- Este arquivo é parte do software django-procedures.

-- django-procedures é um software livre: você pode redistribuí-lo e/ou modificá-lo
-- sob os termos da Licença Pública Geral GNU (GNU General Public License),
-- tal como é publicada pela Free Software Foundation, na versão 3 da
-- licença, ou (sua decisão) qualquer versão posterior.

-- django-procedures é distribuído na esperança de que seja útil, mas SEM NENHUMA
-- GARANTIA; nem mesmo a garantia implícita de VALOR COMERCIAL ou ADEQUAÇÃO
-- PARA UM PROPÓSITO EM PARTICULAR. Veja a Licença Pública Geral GNU para
-- mais detalhes.

-- Você deve ter recebido uma cópia da Licença Pública Geral GNU junto com
-- este programa. Se não, consulte <http://www.gnu.org/licenses/>.

{-# LANGUAGE DeriveGeneric, OverloadedStrings #-}
{-# OPTIONS -fno-warn-unused-do-bind #-}

module ParseUrl where

import qualified GHC.Generics as G
import qualified Data.Aeson as A
import qualified Data.ByteString as B
import qualified Data.ByteString.Lazy as BL
import qualified Data.Text as T
import qualified Text.Parsec as P

import Data.Aeson ((.=))
import Data.Text.Encoding (decodeUtf8)
import Text.Parsec.Text (Parser)
import Control.Monad.Identity (Identity)
import Control.Monad.IO.Class (MonadIO, liftIO)

import Foreign.C
import Control.Applicative
import Text.Parsec.Expr

data Search = Search
	{ field :: T.Text
	, args :: [T.Text]
	} deriving (Show, G.Generic)

instance A.FromJSON Search
instance A.ToJSON Search

data BooleanExpr = And { left :: BooleanExpr, right :: BooleanExpr }
	| Or { left :: BooleanExpr, right :: BooleanExpr }
	| Not BooleanExpr
	| BooleanExpr Search
	deriving (Show, G.Generic)

instance A.FromJSON BooleanExpr
instance A.ToJSON BooleanExpr

newtype PyException = PyExc T.Text deriving (Show, G.Generic)

instance A.FromJSON PyException
instance A.ToJSON PyException where
	toJSON (PyExc text) = A.object
		[ "tag" .= ("PyExc" :: T.Text)
		, "contents" .= text
		]

andOperator :: Parser ()
andOperator = (>> return () ) . P.string . T.unpack $  "/"

orOperator :: Parser ()
orOperator = (P.try (P.string "+") <|> (P.many1 . P.char) ' ') >> return ()

notOperator :: Parser ()
notOperator = (>> return () ) . P.string . T.unpack $ "!"

fieldParser :: Parser T.Text
fieldParser = T.pack <$> P.many1 (P.letter <|> P.digit <|> P.oneOf "_-")

quotedArg :: Parser T.Text
quotedArg = do
	arg <- T.pack <$> P.many (P.noneOf "$\"")
	P.try (escapedSeq "$\"" "\"" arg) <|> P.try (escapedSeq "$$" "$" arg)
		<|> return arg
	where escapedSeq escapeSeq char arg = do
			P.string escapeSeq
			next <- quotedArg
			return . T.concat $ [arg, char, next]

unquotedArg :: Parser T.Text
unquotedArg = T.pack <$> P.many1 (P.letter <|> P.digit <|> P.oneOf "_-")

argParser :: Parser T.Text
argParser = P.try $ do
		P.char '"'
		arg <- quotedArg
		P.char '"'
		return arg
	<|> unquotedArg

search :: Parser Search
search = do
	key <- fieldParser
	P.char ','
	argList <- argParser `P.sepBy1` P.char ','
	return Search { field=key, args=argList }

parensExpr :: Parser BooleanExpr -> Parser BooleanExpr
parensExpr p = do
	P.char '('
	expression <- p
	P.char ')'
	return expression

fullExpr :: Parser BooleanExpr
fullExpr = buildExpressionParser operators singleExpr

singleExpr :: Parser BooleanExpr
singleExpr = parensExpr fullExpr <|> fmap BooleanExpr search

operators :: OperatorTable T.Text () Identity BooleanExpr
operators =
	[ [prefix notOperator Not]
	, [binary andOperator And AssocLeft]
	, [binary orOperator Or AssocLeft]
	]

binary :: Parser () -> (BooleanExpr -> BooleanExpr -> BooleanExpr) -> Assoc
	-> Operator T.Text () Identity BooleanExpr
binary op f = Infix $ op >> return f

prefix :: Parser () -> (BooleanExpr -> BooleanExpr)
	-> Operator T.Text () Identity BooleanExpr
prefix op f = Prefix $ op >> return f

returnObj :: (A.ToJSON a, MonadIO m) => a -> m CString
returnObj = liftIO . flip B.useAsCString return . BL.toStrict . A.encode

foreign export ccall parseUrl :: CString -> IO CString
parseUrl :: CString -> IO CString
parseUrl cUrl = do
	url <- decodeUtf8 <$> B.packCString cUrl
	case P.parse fullExpr "" url of
		Right result -> returnObj result
		Left err -> returnObj . PyExc . T.pack . show $ err

